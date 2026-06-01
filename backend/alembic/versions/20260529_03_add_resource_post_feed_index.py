"""add resource post feed index

Revision ID: 20260529_03
Revises: 20260529_02
Create Date: 2026-05-29

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "20260529_03"
down_revision = "20260529_02"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "ix_resource_posts_status_industry_mode_created",
        "resource_posts",
        ["status", "industry_label", "mode", "created_at"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_resource_posts_status_industry_mode_created",
        table_name="resource_posts",
    )
