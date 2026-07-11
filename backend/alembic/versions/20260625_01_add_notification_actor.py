"""add notification actor

Revision ID: 20260625_01
Revises: 20260616_02
Create Date: 2026-06-25 15:05:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260625_01"
down_revision = "20260616_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("notifications")}
    if "actor_user_pk" not in columns:
        op.add_column(
            "notifications",
            sa.Column("actor_user_pk", sa.Integer(), nullable=True, comment="触发通知的用户ID"),
        )
        op.create_index(
            "ix_notifications_actor_user_pk",
            "notifications",
            ["actor_user_pk"],
            unique=False,
        )
        op.create_foreign_key(
            "fk_notifications_actor_user_pk_users",
            "notifications",
            "users",
            ["actor_user_pk"],
            ["id"],
            ondelete="SET NULL",
        )

    notifications = sa.table(
        "notifications",
        sa.column("id", sa.Integer()),
        sa.column("type", sa.String()),
        sa.column("content", sa.Text()),
        sa.column("actor_user_pk", sa.Integer()),
    )
    users = sa.table(
        "users",
        sa.column("id", sa.Integer()),
        sa.column("nickname", sa.String()),
    )
    user_rows = bind.execute(sa.select(users.c.id, users.c.nickname)).all()
    nickname_users: dict[str, list[int]] = {}
    for user_pk, nickname in user_rows:
        normalized = str(nickname or "").strip()
        if normalized:
            nickname_users.setdefault(normalized, []).append(int(user_pk))

    notification_rows = bind.execute(
        sa.select(notifications.c.id, notifications.c.content).where(
            notifications.c.type == "collection",
            notifications.c.actor_user_pk.is_(None),
        )
    ).all()
    for notification_id, content in notification_rows:
        normalized_content = str(content or "").strip()
        matched_user_pk = None
        for nickname, user_pks in nickname_users.items():
            if len(user_pks) == 1 and normalized_content.startswith(f"{nickname}收藏"):
                matched_user_pk = user_pks[0]
                break
        if matched_user_pk is not None:
            bind.execute(
                notifications.update()
                .where(notifications.c.id == int(notification_id))
                .values(actor_user_pk=matched_user_pk)
            )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {column["name"] for column in inspector.get_columns("notifications")}
    if "actor_user_pk" not in columns:
        return
    foreign_keys = {item.get("name") for item in inspector.get_foreign_keys("notifications")}
    if "fk_notifications_actor_user_pk_users" in foreign_keys:
        op.drop_constraint(
            "fk_notifications_actor_user_pk_users",
            "notifications",
            type_="foreignkey",
        )
    indexes = {item["name"] for item in inspector.get_indexes("notifications")}
    if "ix_notifications_actor_user_pk" in indexes:
        op.drop_index("ix_notifications_actor_user_pk", table_name="notifications")
    op.drop_column("notifications", "actor_user_pk")
