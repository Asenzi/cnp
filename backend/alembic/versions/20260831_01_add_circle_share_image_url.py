"""add circle share image url

Revision ID: 20260831_01
Revises: 20260827_01
Create Date: 2026-08-31 00:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260831_01"
down_revision: str | None = "20260827_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("circles", sa.Column("share_image_url", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("circles", "share_image_url")
