"""add member order client platform

Revision ID: 20260908_01
Revises: 20260831_01
Create Date: 2026-09-08 20:20:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260908_01"
down_revision = "20260831_01"
branch_labels = None
depends_on = None


def _has_table(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _has_index(inspector, table_name: str, index_name: str) -> bool:
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    table_name = "member_orders"
    if not _has_table(inspector, table_name):
        return

    if not _has_column(inspector, table_name, "client_platform"):
        op.add_column(table_name, sa.Column("client_platform", sa.String(length=16), nullable=True))

    inspector = sa.inspect(op.get_bind())
    if not _has_index(inspector, table_name, "ix_member_orders_client_platform"):
        op.create_index("ix_member_orders_client_platform", table_name, ["client_platform"], unique=False)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    table_name = "member_orders"
    if not _has_table(inspector, table_name):
        return

    if _has_index(inspector, table_name, "ix_member_orders_client_platform"):
        op.drop_index("ix_member_orders_client_platform", table_name=table_name)
    if _has_column(inspector, table_name, "client_platform"):
        op.drop_column(table_name, "client_platform")
