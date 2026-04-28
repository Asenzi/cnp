"""add email to users

Revision ID: 20260428_01
Revises: 20260421_01
Create Date: 2026-04-28

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260428_01'
down_revision = '20260421_01'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('email', sa.String(100), nullable=True))


def downgrade():
    op.drop_column('users', 'email')
