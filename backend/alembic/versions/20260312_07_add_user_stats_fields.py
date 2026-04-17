"""add user stats fields for me page

Revision ID: 2026031207
Revises: 2026031206
Create Date: 2026-03-12 18:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026031207"
down_revision: str | None = "2026031206"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("circle_count", sa.Integer(), nullable=False, server_default=sa.text("0")))
    op.add_column("users", sa.Column("network_count", sa.Integer(), nullable=False, server_default=sa.text("0")))
    op.add_column(
        "users",
        sa.Column("balance", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0.00")),
    )

    op.execute("UPDATE users SET circle_count = 0 WHERE circle_count IS NULL")
    op.execute("UPDATE users SET network_count = 0 WHERE network_count IS NULL")
    op.execute("UPDATE users SET balance = 0.00 WHERE balance IS NULL")


def downgrade() -> None:
    op.drop_column("users", "balance")
    op.drop_column("users", "network_count")
    op.drop_column("users", "circle_count")
