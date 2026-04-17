"""add user_no and is_verified to users

Revision ID: 2026031203
Revises: 2026031202
Create Date: 2026-03-12 15:10:00
"""

from collections.abc import Sequence
import random
import time

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026031203"
down_revision: str | None = "2026031202"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _generate_user_no() -> str:
    timestamp_tail = str(int(time.time() * 1000))[-5:]
    random_tail = f"{random.randint(0, 999):03d}"
    return f"{timestamp_tail}{random_tail}"


def upgrade() -> None:
    op.add_column("users", sa.Column("user_no", sa.String(length=8), nullable=True))
    op.add_column(
        "users",
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    op.create_index("ix_users_user_no", "users", ["user_no"], unique=True)

    bind = op.get_bind()
    existing_user_no = {
        row[0]
        for row in bind.execute(sa.text("SELECT user_no FROM users WHERE user_no IS NOT NULL"))
    }
    user_rows = bind.execute(sa.text("SELECT id FROM users WHERE user_no IS NULL ORDER BY id")).fetchall()

    for (pk,) in user_rows:
        for _ in range(100):
            candidate = _generate_user_no()
            if candidate in existing_user_no:
                continue
            bind.execute(
                sa.text("UPDATE users SET user_no = :user_no WHERE id = :id"),
                {"user_no": candidate, "id": pk},
            )
            existing_user_no.add(candidate)
            break
        else:
            raise RuntimeError(f"Unable to generate unique user_no for user id={pk}")

    op.alter_column(
        "users",
        "user_no",
        existing_type=sa.String(length=8),
        nullable=False,
    )


def downgrade() -> None:
    op.drop_index("ix_users_user_no", table_name="users")
    op.drop_column("users", "is_verified")
    op.drop_column("users", "user_no")
