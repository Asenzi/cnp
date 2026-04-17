"""add user profile editable fields

Revision ID: 2026031205
Revises: 2026031204
Create Date: 2026-03-12 16:15:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026031205"
down_revision: str | None = "2026031204"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("industry_code", sa.String(length=32), nullable=True))
    op.add_column("users", sa.Column("industry_label", sa.String(length=64), nullable=True))
    op.add_column(
        "users",
        sa.Column("show_contact", sa.Boolean(), nullable=False, server_default=sa.text("1")),
    )


def downgrade() -> None:
    op.drop_column("users", "show_contact")
    op.drop_column("users", "industry_label")
    op.drop_column("users", "industry_code")
