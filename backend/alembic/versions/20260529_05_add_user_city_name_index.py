"""add user city_name index

Revision ID: 20260529_05
Revises: 20260529_04
Create Date: 2026-05-29

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "20260529_05"
down_revision = "20260529_04"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "ix_users_city_name",
        "users",
        ["city_name"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_users_city_name",
        table_name="users",
    )
