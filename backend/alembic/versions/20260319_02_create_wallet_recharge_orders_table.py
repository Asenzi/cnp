"""create wallet recharge orders table

Revision ID: 2026031902
Revises: 2026031901
Create Date: 2026-03-19 23:50:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026031902"
down_revision: str | None = "2026031901"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "wallet_recharge_orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_no", sa.String(length=32), nullable=False),
        sa.Column("user_pk", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False, server_default=sa.text("0.00")),
        sa.Column("pay_channel", sa.String(length=16), nullable=False, server_default=sa.text("'wxpay'")),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("transaction_id", sa.String(length=64), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_wallet_recharge_orders_order_no", "wallet_recharge_orders", ["order_no"], unique=True)
    op.create_index("ix_wallet_recharge_orders_user_pk", "wallet_recharge_orders", ["user_pk"], unique=False)
    op.create_index("ix_wallet_recharge_orders_status", "wallet_recharge_orders", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_wallet_recharge_orders_status", table_name="wallet_recharge_orders")
    op.drop_index("ix_wallet_recharge_orders_user_pk", table_name="wallet_recharge_orders")
    op.drop_index("ix_wallet_recharge_orders_order_no", table_name="wallet_recharge_orders")
    op.drop_table("wallet_recharge_orders")
