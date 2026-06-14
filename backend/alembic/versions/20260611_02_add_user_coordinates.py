"""add user coordinates

Revision ID: 20260611_02
Revises: 20260611_01
Create Date: 2026-06-11 21:30:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260611_02"
down_revision = "20260611_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {item["name"] for item in inspector.get_columns("users")}

    if "latitude" not in columns:
        op.add_column(
            "users",
            sa.Column("latitude", sa.Numeric(precision=10, scale=7), nullable=True),
        )
    if "longitude" not in columns:
        op.add_column(
            "users",
            sa.Column("longitude", sa.Numeric(precision=10, scale=7), nullable=True),
        )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {item["name"] for item in inspector.get_columns("users")}

    if "longitude" in columns:
        op.drop_column("users", "longitude")
    if "latitude" in columns:
        op.drop_column("users", "latitude")
