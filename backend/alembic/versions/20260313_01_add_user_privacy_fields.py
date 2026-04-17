"""add user privacy setting fields

Revision ID: 2026031301
Revises: 2026031212
Create Date: 2026-03-13 10:10:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026031301"
down_revision: str | None = "2026031212"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("protect_real_name", sa.Boolean(), nullable=False, server_default=sa.text("1")),
    )
    op.add_column(
        "users",
        sa.Column("allow_find_by_email", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "users",
        sa.Column("friend_request_scope", sa.String(length=32), nullable=False, server_default=sa.text("'all'")),
    )
    op.add_column(
        "users",
        sa.Column(
            "message_scope",
            sa.String(length=32),
            nullable=False,
            server_default=sa.text("'friends_or_contacts'"),
        ),
    )
    op.add_column(
        "users",
        sa.Column("allow_auto_add_friend", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )

    # Phone visibility should be hidden by default.
    op.execute("UPDATE users SET show_contact = 0")
    op.alter_column(
        "users",
        "show_contact",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.text("0"),
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "show_contact",
        existing_type=sa.Boolean(),
        nullable=False,
        server_default=sa.text("1"),
    )
    op.drop_column("users", "allow_auto_add_friend")
    op.drop_column("users", "message_scope")
    op.drop_column("users", "friend_request_scope")
    op.drop_column("users", "allow_find_by_email")
    op.drop_column("users", "protect_real_name")
