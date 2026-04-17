"""add job title to users

Revision ID: 2026032301
Revises: 2026031902
Create Date: 2026-03-23 14:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026032301"
down_revision: str | None = "2026031902"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("job_title", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "job_title")
