"""create user follows table

Revision ID: 20260609_01
Revises: 20260603_01
Create Date: 2026-06-09 14:30:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = "20260609_01"
down_revision = "20260603_01"
branch_labels = None
depends_on = None


def _table_exists(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in set(inspector.get_table_names())


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # 创建用户关注表
    if not _table_exists(inspector, "user_follows"):
        op.create_table(
            "user_follows",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column(
                "follower_user_pk",
                sa.Integer(),
                nullable=False,
                comment="关注者用户ID"
            ),
            sa.Column(
                "following_user_pk",
                sa.Integer(),
                nullable=False,
                comment="被关注的用户ID"
            ),
            sa.Column(
                "created_at",
                sa.DateTime(),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
                comment="关注时间"
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
                nullable=False,
                comment="更新时间"
            ),
            sa.ForeignKeyConstraint(
                ["follower_user_pk"],
                ["users.id"],
                name="fk_user_follows_follower",
                ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(
                ["following_user_pk"],
                ["users.id"],
                name="fk_user_follows_following",
                ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "follower_user_pk",
                "following_user_pk",
                name="uq_user_follow"
            ),
            mysql_charset="utf8mb4",
            mysql_collate="utf8mb4_unicode_ci",
            mysql_engine="InnoDB"
        )

        # 创建索引
        op.create_index(
            "ix_user_follows_follower_user_pk",
            "user_follows",
            ["follower_user_pk"],
            unique=False
        )
        op.create_index(
            "ix_user_follows_following_user_pk",
            "user_follows",
            ["following_user_pk"],
            unique=False
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _table_exists(inspector, "user_follows"):
        op.drop_table("user_follows")
