"""Add user district for nearby discovery cards."""
from alembic import op
import sqlalchemy as sa

revision = "20261013_03"
down_revision = "20261013_02"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("district_name", sa.String(length=32), nullable=True))


def downgrade():
    op.drop_column("users", "district_name")
