"""add user password hash

Revision ID: 2026031211
Revises: 2026031210
Create Date: 2026-03-12 22:10:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026031211"
down_revision: str | None = "2026031210"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.String(length=128), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "password_hash")
