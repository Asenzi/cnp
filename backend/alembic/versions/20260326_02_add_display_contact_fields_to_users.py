"""add display contact fields to users

Revision ID: 2026032602
Revises: 2026032601
Create Date: 2026-03-26 16:40:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026032602"
down_revision: str | None = "2026032601"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("display_phone", sa.String(length=20), nullable=True))
    op.add_column("users", sa.Column("display_wechat", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "display_wechat")
    op.drop_column("users", "display_phone")
