"""allow empty user nickname and avatar

Revision ID: 20260827_01
Revises: 20260709_02
Create Date: 2026-08-27 15:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260827_01"
down_revision: str | None = "20260709_02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "nickname",
        existing_type=sa.String(length=64),
        nullable=True,
    )
    op.alter_column(
        "users",
        "avatar_url",
        existing_type=sa.String(length=255),
        nullable=True,
        server_default=None,
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE users
        SET nickname = CONCAT('用户', RIGHT(phone, 4))
        WHERE nickname IS NULL OR TRIM(nickname) = ''
        """
    )
    op.execute(
        """
        UPDATE users
        SET avatar_url = '/static/logo.png'
        WHERE avatar_url IS NULL OR TRIM(avatar_url) = ''
        """
    )
    op.alter_column(
        "users",
        "nickname",
        existing_type=sa.String(length=64),
        nullable=False,
    )
    op.alter_column(
        "users",
        "avatar_url",
        existing_type=sa.String(length=255),
        nullable=False,
        server_default=sa.text("'/static/logo.png'"),
    )
