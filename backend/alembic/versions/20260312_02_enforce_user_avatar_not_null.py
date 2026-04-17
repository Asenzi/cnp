"""enforce user avatar not null

Revision ID: 2026031202
Revises: 2026031201
Create Date: 2026-03-12 14:40:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026031202"
down_revision: str | None = "2026031201"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Backfill historical records before adding NOT NULL constraint.
    op.execute(
        """
        UPDATE users
        SET avatar_url = '/static/logo.png'
        WHERE avatar_url IS NULL OR TRIM(avatar_url) = ''
        """
    )

    op.alter_column(
        "users",
        "avatar_url",
        existing_type=sa.String(length=255),
        nullable=False,
        server_default=sa.text("'/static/logo.png'"),
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "avatar_url",
        existing_type=sa.String(length=255),
        nullable=True,
        server_default=None,
    )
