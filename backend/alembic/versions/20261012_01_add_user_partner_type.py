"""add user partner type

Revision ID: 20261012_01
Revises: 20260908_01
Create Date: 2026-10-12 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20261012_01"
down_revision = "20260908_01"
branch_labels = None
depends_on = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _has_index(inspector, table_name: str, index_name: str) -> bool:
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "users" not in inspector.get_table_names():
        return
    if not _has_column(inspector, "users", "partner_type"):
        op.add_column(
            "users",
            sa.Column("partner_type", sa.String(length=24), nullable=True, comment="合作身份: salon_owner / city_partner"),
        )
    inspector = sa.inspect(op.get_bind())
    if not _has_index(inspector, "users", "ix_users_partner_type"):
        op.create_index("ix_users_partner_type", "users", ["partner_type"], unique=False)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "users" not in inspector.get_table_names():
        return
    if _has_index(inspector, "users", "ix_users_partner_type"):
        op.drop_index("ix_users_partner_type", table_name="users")
    if _has_column(inspector, "users", "partner_type"):
        op.drop_column("users", "partner_type")
