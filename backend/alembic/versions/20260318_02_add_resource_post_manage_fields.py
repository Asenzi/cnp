"""add resource post manage fields

Revision ID: 2026031802
Revises: 2026031801
Create Date: 2026-03-18 23:59:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026031802"
down_revision: str | None = "2026031801"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("resource_posts", sa.Column("is_pinned", sa.Boolean(), nullable=False, server_default=sa.text("0")))
    op.add_column("resource_posts", sa.Column("pinned_at", sa.DateTime(), nullable=True))
    op.create_index("ix_resource_posts_is_pinned", "resource_posts", ["is_pinned"], unique=False)
    op.create_index("ix_resource_posts_pinned_at", "resource_posts", ["pinned_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_resource_posts_pinned_at", table_name="resource_posts")
    op.drop_index("ix_resource_posts_is_pinned", table_name="resource_posts")
    op.drop_column("resource_posts", "pinned_at")
    op.drop_column("resource_posts", "is_pinned")
