"""add external split fields

Revision ID: 20260616_02
Revises: 20260616_01
Create Date: 2026-06-16 22:20:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260616_02"
down_revision = "20260616_01"
branch_labels = None
depends_on = None


def _has_table(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _add_column_if_missing(inspector, table_name: str, column_name: str, column) -> None:
    if not _has_column(inspector, table_name, column_name):
        op.add_column(table_name, column)


def _add_index_if_missing(inspector, table_name: str, index_name: str, columns: list[str]) -> None:
    if index_name not in {index["name"] for index in inspector.get_indexes(table_name)}:
        op.create_index(index_name, table_name, columns, unique=False)


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    table_name = "split_transactions"
    if not _has_table(inspector, table_name):
        return

    _add_column_if_missing(inspector, table_name, "channel", sa.Column("channel", sa.String(length=32), nullable=True))
    _add_column_if_missing(
        inspector,
        table_name,
        "receiver_openid",
        sa.Column("receiver_openid", sa.String(length=128), nullable=True),
    )
    _add_column_if_missing(
        inspector,
        table_name,
        "external_transaction_id",
        sa.Column("external_transaction_id", sa.String(length=128), nullable=True),
    )
    _add_column_if_missing(
        inspector,
        table_name,
        "external_order_no",
        sa.Column("external_order_no", sa.String(length=64), nullable=True),
    )
    _add_column_if_missing(
        inspector,
        table_name,
        "external_status",
        sa.Column("external_status", sa.String(length=32), nullable=True),
    )
    _add_column_if_missing(
        inspector,
        table_name,
        "external_error",
        sa.Column("external_error", sa.Text(), nullable=True),
    )

    inspector = sa.inspect(op.get_bind())
    _add_index_if_missing(inspector, table_name, "ix_split_transactions_channel", ["channel"])
    _add_index_if_missing(
        inspector,
        table_name,
        "ix_split_transactions_external_transaction_id",
        ["external_transaction_id"],
    )
    _add_index_if_missing(inspector, table_name, "ix_split_transactions_external_order_no", ["external_order_no"])
    _add_index_if_missing(inspector, table_name, "ix_split_transactions_external_status", ["external_status"])


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    table_name = "split_transactions"
    if not _has_table(inspector, table_name):
        return

    for index_name in (
        "ix_split_transactions_external_status",
        "ix_split_transactions_external_order_no",
        "ix_split_transactions_external_transaction_id",
        "ix_split_transactions_channel",
    ):
        if index_name in {index["name"] for index in inspector.get_indexes(table_name)}:
            op.drop_index(index_name, table_name=table_name)

    inspector = sa.inspect(op.get_bind())
    for column_name in (
        "external_error",
        "external_status",
        "external_order_no",
        "external_transaction_id",
        "receiver_openid",
        "channel",
    ):
        if _has_column(inspector, table_name, column_name):
            op.drop_column(table_name, column_name)
