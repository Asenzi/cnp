"""add circle avatar_url

Revision ID: 2026031304
Revises: 2026031303
Create Date: 2026-03-13 23:58:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026031304"
down_revision: str | None = "2026031303"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("circles", sa.Column("avatar_url", sa.String(length=255), nullable=True))
    op.execute("UPDATE circles SET avatar_url = cover_url WHERE avatar_url IS NULL OR avatar_url = ''")
    op.alter_column("circles", "avatar_url", existing_type=sa.String(length=255), nullable=False)


def downgrade() -> None:
    op.drop_column("circles", "avatar_url")
