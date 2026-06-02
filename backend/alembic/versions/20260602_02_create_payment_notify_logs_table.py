"""create payment notify logs table

Revision ID: 20260602_02
Revises: 20260602_01
Create Date: 2026-06-02 16:30:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260602_02"
down_revision = "20260602_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "payment_notify_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_no", sa.String(length=32), nullable=False, comment="订单号"),
        sa.Column("notify_type", sa.String(length=32), nullable=False, comment="通知类型: wxpay, alipay等"),
        sa.Column("raw_body", sa.Text(), nullable=True, comment="原始请求体"),
        sa.Column("result", sa.String(length=16), nullable=False, comment="处理结果: success, failed"),
        sa.Column("result_message", sa.String(length=255), nullable=True, comment="结果消息"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_payment_notify_logs_order_no"), "payment_notify_logs", ["order_no"], unique=False)
    op.create_index(op.f("ix_payment_notify_logs_notify_type"), "payment_notify_logs", ["notify_type"], unique=False)
    op.create_index(op.f("ix_payment_notify_logs_result"), "payment_notify_logs", ["result"], unique=False)
    op.create_index(op.f("ix_payment_notify_logs_created_at"), "payment_notify_logs", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_payment_notify_logs_created_at"), table_name="payment_notify_logs")
    op.drop_index(op.f("ix_payment_notify_logs_result"), table_name="payment_notify_logs")
    op.drop_index(op.f("ix_payment_notify_logs_notify_type"), table_name="payment_notify_logs")
    op.drop_index(op.f("ix_payment_notify_logs_order_no"), table_name="payment_notify_logs")
    op.drop_table("payment_notify_logs")
