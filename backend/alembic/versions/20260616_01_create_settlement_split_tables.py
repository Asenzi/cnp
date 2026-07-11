"""create settlement split tables

Revision ID: 20260616_01
Revises: 20260611_02
Create Date: 2026-06-16 21:30:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260616_01"
down_revision = "20260611_02"
branch_labels = None
depends_on = None


def _has_table(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "split_rules"):
        op.create_table(
            "split_rules",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("biz_type", sa.String(length=64), nullable=False),
            sa.Column("role_type", sa.String(length=32), nullable=False),
            sa.Column("split_type", sa.String(length=16), server_default=sa.text("'percentage'"), nullable=False),
            sa.Column("split_value", sa.Numeric(12, 4), server_default=sa.text("0.0000"), nullable=False),
            sa.Column("priority", sa.Integer(), server_default=sa.text("100"), nullable=False),
            sa.Column("enabled", sa.Boolean(), server_default=sa.text("1"), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("biz_type", "role_type", name="uq_split_rules_biz_role"),
        )
        op.create_index(op.f("ix_split_rules_biz_type"), "split_rules", ["biz_type"], unique=False)
        op.create_index(op.f("ix_split_rules_role_type"), "split_rules", ["role_type"], unique=False)

    if not _has_table(inspector, "user_settlements"):
        op.create_table(
            "user_settlements",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_pk", sa.Integer(), nullable=False),
            sa.Column("available_balance", sa.Numeric(12, 2), server_default=sa.text("0.00"), nullable=False),
            sa.Column("frozen_balance", sa.Numeric(12, 2), server_default=sa.text("0.00"), nullable=False),
            sa.Column("total_income", sa.Numeric(12, 2), server_default=sa.text("0.00"), nullable=False),
            sa.Column("total_withdrawn", sa.Numeric(12, 2), server_default=sa.text("0.00"), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["user_pk"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_user_settlements_user_pk"), "user_settlements", ["user_pk"], unique=True)

    if not _has_table(inspector, "split_transactions"):
        op.create_table(
            "split_transactions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("order_no", sa.String(length=64), nullable=False),
            sa.Column("biz_type", sa.String(length=64), nullable=False),
            sa.Column("split_from_user_pk", sa.Integer(), nullable=False),
            sa.Column("split_to_user_pk", sa.Integer(), nullable=False),
            sa.Column("role_type", sa.String(length=32), nullable=False),
            sa.Column("total_amount", sa.Numeric(12, 2), server_default=sa.text("0.00"), nullable=False),
            sa.Column("split_amount", sa.Numeric(12, 2), server_default=sa.text("0.00"), nullable=False),
            sa.Column("platform_fee", sa.Numeric(12, 2), server_default=sa.text("0.00"), nullable=False),
            sa.Column("split_status", sa.String(length=16), server_default=sa.text("'pending'"), nullable=False),
            sa.Column("channel", sa.String(length=32), nullable=True),
            sa.Column("receiver_openid", sa.String(length=128), nullable=True),
            sa.Column("external_transaction_id", sa.String(length=128), nullable=True),
            sa.Column("external_order_no", sa.String(length=64), nullable=True),
            sa.Column("external_status", sa.String(length=32), nullable=True),
            sa.Column("external_error", sa.Text(), nullable=True),
            sa.Column("freeze_until", sa.DateTime(), nullable=True),
            sa.Column("executed_at", sa.DateTime(), nullable=True),
            sa.Column("remark", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["split_from_user_pk"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["split_to_user_pk"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("order_no", "split_to_user_pk", name="uq_split_transactions_order_user"),
        )
        op.create_index(op.f("ix_split_transactions_biz_type"), "split_transactions", ["biz_type"], unique=False)
        op.create_index(op.f("ix_split_transactions_channel"), "split_transactions", ["channel"], unique=False)
        op.create_index(
            op.f("ix_split_transactions_external_order_no"),
            "split_transactions",
            ["external_order_no"],
            unique=False,
        )
        op.create_index(
            op.f("ix_split_transactions_external_status"),
            "split_transactions",
            ["external_status"],
            unique=False,
        )
        op.create_index(
            op.f("ix_split_transactions_external_transaction_id"),
            "split_transactions",
            ["external_transaction_id"],
            unique=False,
        )
        op.create_index(op.f("ix_split_transactions_freeze_until"), "split_transactions", ["freeze_until"], unique=False)
        op.create_index(op.f("ix_split_transactions_order_no"), "split_transactions", ["order_no"], unique=False)
        op.create_index(op.f("ix_split_transactions_split_from_user_pk"), "split_transactions", ["split_from_user_pk"], unique=False)
        op.create_index(op.f("ix_split_transactions_split_status"), "split_transactions", ["split_status"], unique=False)
        op.create_index(op.f("ix_split_transactions_split_to_user_pk"), "split_transactions", ["split_to_user_pk"], unique=False)

    if not _has_table(inspector, "withdrawal_orders"):
        op.create_table(
            "withdrawal_orders",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("order_no", sa.String(length=64), nullable=False),
            sa.Column("user_pk", sa.Integer(), nullable=False),
            sa.Column("amount", sa.Numeric(12, 2), server_default=sa.text("0.00"), nullable=False),
            sa.Column("fee", sa.Numeric(12, 2), server_default=sa.text("0.00"), nullable=False),
            sa.Column("actual_amount", sa.Numeric(12, 2), server_default=sa.text("0.00"), nullable=False),
            sa.Column("withdraw_type", sa.String(length=32), server_default=sa.text("'wechat'"), nullable=False),
            sa.Column("withdraw_account", sa.String(length=128), nullable=True),
            sa.Column("status", sa.String(length=16), server_default=sa.text("'pending'"), nullable=False),
            sa.Column("transaction_id", sa.String(length=128), nullable=True),
            sa.Column("remark", sa.Text(), nullable=True),
            sa.Column("processed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["user_pk"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_withdrawal_orders_order_no"), "withdrawal_orders", ["order_no"], unique=True)
        op.create_index(op.f("ix_withdrawal_orders_status"), "withdrawal_orders", ["status"], unique=False)
        op.create_index(op.f("ix_withdrawal_orders_user_pk"), "withdrawal_orders", ["user_pk"], unique=False)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    for table_name in ("withdrawal_orders", "split_transactions", "user_settlements", "split_rules"):
        if _has_table(inspector, table_name):
            op.drop_table(table_name)
