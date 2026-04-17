"""rename user_no to user_id

Revision ID: 2026031204
Revises: 2026031203
Create Date: 2026-03-12 15:35:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026031204"
down_revision: str | None = "2026031203"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("ix_users_user_no", table_name="users")
    op.alter_column(
        "users",
        "user_no",
        new_column_name="user_id",
        existing_type=sa.String(length=8),
        existing_nullable=False,
    )
    op.create_index("ix_users_user_id", "users", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_user_id", table_name="users")
    op.alter_column(
        "users",
        "user_id",
        new_column_name="user_no",
        existing_type=sa.String(length=8),
        existing_nullable=False,
    )
    op.create_index("ix_users_user_no", "users", ["user_no"], unique=True)
