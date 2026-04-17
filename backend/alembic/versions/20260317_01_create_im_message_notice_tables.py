"""create im message and system notice tables

Revision ID: 2026031701
Revises: 2026031502
Create Date: 2026-03-17 23:55:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026031701"
down_revision: str | None = "2026031502"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_friend_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("requester_user_pk", sa.Integer(), nullable=False),
        sa.Column("target_user_pk", sa.Integer(), nullable=False),
        sa.Column("request_message", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("handled_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["requester_user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_user_friend_requests_requester_user_pk",
        "user_friend_requests",
        ["requester_user_pk"],
        unique=False,
    )
    op.create_index(
        "idx_user_friend_requests_target_user_pk",
        "user_friend_requests",
        ["target_user_pk"],
        unique=False,
    )
    op.create_index("idx_user_friend_requests_status", "user_friend_requests", ["status"], unique=False)
    op.create_index("idx_user_friend_requests_created_at", "user_friend_requests", ["created_at"], unique=False)
    op.create_index(
        "idx_user_friend_requests_target_status",
        "user_friend_requests",
        ["target_user_pk", "status"],
        unique=False,
    )

    # Backfill pending requests from historical one-way active connections.
    op.execute(
        sa.text(
            """
            INSERT INTO user_friend_requests (
                requester_user_pk,
                target_user_pk,
                request_message,
                status,
                created_at,
                handled_at
            )
            SELECT
                uc.user_pk,
                uc.target_user_pk,
                NULL,
                'pending',
                uc.created_at,
                NULL
            FROM user_connections uc
            WHERE uc.is_active = 1
              AND uc.target_user_pk IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1
                  FROM user_connections rev
                  WHERE rev.user_pk = uc.target_user_pk
                    AND rev.target_user_pk = uc.user_pk
                    AND rev.is_active = 1
              )
            """
        )
    )

    op.create_table(
        "user_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("sender_user_pk", sa.Integer(), nullable=False),
        sa.Column("receiver_user_pk", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(length=16), nullable=False, server_default="text"),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["sender_user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["receiver_user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_user_messages_sender_user_pk", "user_messages", ["sender_user_pk"], unique=False)
    op.create_index("idx_user_messages_receiver_user_pk", "user_messages", ["receiver_user_pk"], unique=False)
    op.create_index("idx_user_messages_is_read", "user_messages", ["is_read"], unique=False)
    op.create_index("idx_user_messages_created_at", "user_messages", ["created_at"], unique=False)
    op.create_index(
        "idx_user_messages_sender_receiver",
        "user_messages",
        ["sender_user_pk", "receiver_user_pk"],
        unique=False,
    )
    op.create_index(
        "idx_user_messages_receiver_is_read",
        "user_messages",
        ["receiver_user_pk", "is_read"],
        unique=False,
    )

    op.create_table(
        "system_notices",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("target_user_pk", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=64), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["target_user_pk"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_system_notices_target_user_pk", "system_notices", ["target_user_pk"], unique=False)
    op.create_index("idx_system_notices_is_read", "system_notices", ["is_read"], unique=False)
    op.create_index("idx_system_notices_created_at", "system_notices", ["created_at"], unique=False)

    notice_table = sa.table(
        "system_notices",
        sa.column("target_user_pk", sa.Integer()),
        sa.column("title", sa.String(length=64)),
        sa.column("content", sa.Text()),
        sa.column("is_read", sa.Boolean()),
    )
    op.bulk_insert(
        notice_table,
        [
            {
                "target_user_pk": None,
                "title": "系统通知",
                "content": "欢迎使用圈脉链，完善资料可获得更精准的人脉推荐。",
                "is_read": False,
            },
            {
                "target_user_pk": None,
                "title": "安全提醒",
                "content": "请勿向陌生人泄露验证码与账号密码。",
                "is_read": True,
            },
        ],
    )


def downgrade() -> None:
    op.drop_index("idx_system_notices_created_at", table_name="system_notices")
    op.drop_index("idx_system_notices_is_read", table_name="system_notices")
    op.drop_index("idx_system_notices_target_user_pk", table_name="system_notices")
    op.drop_table("system_notices")

    op.drop_index("idx_user_messages_receiver_is_read", table_name="user_messages")
    op.drop_index("idx_user_messages_sender_receiver", table_name="user_messages")
    op.drop_index("idx_user_messages_created_at", table_name="user_messages")
    op.drop_index("idx_user_messages_is_read", table_name="user_messages")
    op.drop_index("idx_user_messages_receiver_user_pk", table_name="user_messages")
    op.drop_index("idx_user_messages_sender_user_pk", table_name="user_messages")
    op.drop_table("user_messages")

    op.drop_index("idx_user_friend_requests_target_status", table_name="user_friend_requests")
    op.drop_index("idx_user_friend_requests_created_at", table_name="user_friend_requests")
    op.drop_index("idx_user_friend_requests_status", table_name="user_friend_requests")
    op.drop_index("idx_user_friend_requests_target_user_pk", table_name="user_friend_requests")
    op.drop_index("idx_user_friend_requests_requester_user_pk", table_name="user_friend_requests")
    op.drop_table("user_friend_requests")
