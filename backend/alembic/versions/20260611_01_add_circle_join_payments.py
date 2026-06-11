"""add circle join payment fields

Revision ID: 20260611_01
Revises: 20260610_01
Create Date: 2026-06-11 12:30:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260611_01"
down_revision = "20260610_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {item["name"] for item in inspector.get_columns("circle_join_requests")}

    additions = [
        ("order_no", sa.Column("order_no", sa.String(length=32), nullable=True)),
        ("amount", sa.Column("amount", sa.Numeric(10, 2), server_default=sa.text("0.00"), nullable=False)),
        ("pay_channel", sa.Column("pay_channel", sa.String(length=16), nullable=True)),
        ("payment_status", sa.Column("payment_status", sa.String(length=16), server_default=sa.text("'unpaid'"), nullable=False)),
        ("transaction_id", sa.Column("transaction_id", sa.String(length=64), nullable=True)),
        ("refund_status", sa.Column("refund_status", sa.String(length=16), server_default=sa.text("'none'"), nullable=False)),
        ("paid_at", sa.Column("paid_at", sa.DateTime(), nullable=True)),
        ("refunded_at", sa.Column("refunded_at", sa.DateTime(), nullable=True)),
        ("auto_approve_at", sa.Column("auto_approve_at", sa.DateTime(), nullable=True)),
    ]
    for name, column in additions:
        if name not in columns:
            op.add_column("circle_join_requests", column)

    indexes = {item["name"] for item in inspector.get_indexes("circle_join_requests")}
    if "ix_circle_join_requests_order_no" not in indexes:
        op.create_index("ix_circle_join_requests_order_no", "circle_join_requests", ["order_no"], unique=True)
    if "ix_circle_join_requests_payment_status" not in indexes:
        op.create_index("ix_circle_join_requests_payment_status", "circle_join_requests", ["payment_status"], unique=False)
    if "ix_circle_join_requests_auto_approve_at" not in indexes:
        op.create_index("ix_circle_join_requests_auto_approve_at", "circle_join_requests", ["auto_approve_at"], unique=False)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    indexes = {item["name"] for item in inspector.get_indexes("circle_join_requests")}
    for name in (
        "ix_circle_join_requests_auto_approve_at",
        "ix_circle_join_requests_payment_status",
        "ix_circle_join_requests_order_no",
    ):
        if name in indexes:
            op.drop_index(name, table_name="circle_join_requests")

    columns = {item["name"] for item in inspector.get_columns("circle_join_requests")}
    for name in (
        "auto_approve_at",
        "refunded_at",
        "paid_at",
        "refund_status",
        "transaction_id",
        "payment_status",
        "pay_channel",
        "amount",
        "order_no",
    ):
        if name in columns:
            op.drop_column("circle_join_requests", name)
