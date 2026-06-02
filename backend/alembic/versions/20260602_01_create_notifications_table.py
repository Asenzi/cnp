"""create notifications table

Revision ID: 20260602_01
Revises: 20260601_01
Create Date: 2026-06-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260602_01"
down_revision = "20260601_01"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="通知ID"),
        sa.Column("user_pk", sa.Integer(), nullable=False, comment="用户ID"),
        sa.Column(
            "type",
            sa.String(length=50),
            nullable=False,
            server_default=sa.text("'system'"),
            comment="通知类型: system, circle, event, post",
        ),
        sa.Column("title", sa.String(length=200), nullable=False, comment="通知标题"),
        sa.Column("content", sa.Text(), nullable=False, comment="通知内容"),
        sa.Column("link_type", sa.String(length=50), nullable=True, comment="链接类型: circle, event, post, user, none"),
        sa.Column("link_id", sa.String(length=100), nullable=True, comment="关联ID"),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("0"), comment="是否已读"),
        sa.Column("read_at", sa.DateTime(), nullable=True, comment="阅读时间"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="更新时间"),
        sa.ForeignKeyConstraint(["user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_id", "notifications", ["id"], unique=False)
    op.create_index("ix_notifications_user_pk", "notifications", ["user_pk"], unique=False)
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"], unique=False)
    op.create_index("ix_notifications_user_read", "notifications", ["user_pk", "is_read"], unique=False)
    op.create_index("ix_notifications_user_created", "notifications", ["user_pk", "created_at"], unique=False)


def downgrade():
    op.drop_index("ix_notifications_user_created", table_name="notifications")
    op.drop_index("ix_notifications_user_read", table_name="notifications")
    op.drop_index("ix_notifications_is_read", table_name="notifications")
    op.drop_index("ix_notifications_user_pk", table_name="notifications")
    op.drop_index("ix_notifications_id", table_name="notifications")
    op.drop_table("notifications")
