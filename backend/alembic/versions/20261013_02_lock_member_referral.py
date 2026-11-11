"""Persist first membership conversion attribution."""
from alembic import op
import sqlalchemy as sa

revision = "20261013_02"
down_revision = "20261013_01"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("member_referral_snapshot", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("users", "member_referral_snapshot")
