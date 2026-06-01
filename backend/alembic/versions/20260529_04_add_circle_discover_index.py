"""add circle discover index

Revision ID: 20260529_04
Revises: 20260529_03
Create Date: 2026-05-29

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "20260529_04"
down_revision = "20260529_03"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "ix_circles_status_industry_active_created",
        "circles",
        ["status", "industry_label", "last_active_at", "created_at"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_circles_status_industry_active_created",
        table_name="circles",
    )
