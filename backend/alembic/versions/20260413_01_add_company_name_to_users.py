"""add company_name to users

Revision ID: 2026041301
Revises: 2026032901
Create Date: 2026-04-13 12:05:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026041301"
down_revision: str | None = "2026032901"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("company_name", sa.String(length=128), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "company_name")
