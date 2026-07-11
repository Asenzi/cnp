"""add wechat session key for virtual payment

Revision ID: 20260703_01
Revises: 20260702_01
Create Date: 2026-07-03 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260703_01"
down_revision = "20260702_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("wechat_session_key", sa.String(length=128), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "wechat_session_key")
