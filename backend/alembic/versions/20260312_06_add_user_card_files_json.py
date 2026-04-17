"""add card files json field for user profile

Revision ID: 2026031206
Revises: 2026031205
Create Date: 2026-03-12 16:45:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026031206"
down_revision: str | None = "2026031205"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("card_files_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "card_files_json")
