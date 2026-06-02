"""create wallet transactions table

Revision ID: 20260602_01
Revises:
Create Date: 2026-06-02 16:03:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260602_01"
down_revision = None  # 请根据你的最新迁移版本填写
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "wallet_transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_pk", sa.Integer(), nullable=False),
        sa.Column("change_amount", sa.Numeric(precision=12, scale=2), nullable=False, comment="变动金额，正数为收入，负数为支出"),
        sa.Column("balance_after", sa.Numeric(precision=12, scale=2), nullable=False, server_default=sa.text("0.00"), comment="交易后余额"),
        sa.Column("biz_type", sa.String(length=64), nullable=False, comment="业务类型: recharge-充值, member_subscribe-会员订阅, refund-退款等"),
        sa.Column("biz_key", sa.String(length=128), nullable=False, server_default=sa.text("''"), comment="业务唯一标识，如订单号"),
        sa.Column("title", sa.String(length=128), nullable=False, server_default=sa.text("''"), comment="交易标题"),
        sa.Column("remark", sa.Text(), nullable=True, comment="备注信息"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_pk", "biz_type", "biz_key", name="uq_wallet_transactions_user_biz"),
    )
    op.create_index(op.f("ix_wallet_transactions_user_pk"), "wallet_transactions", ["user_pk"], unique=False)
    op.create_index(op.f("ix_wallet_transactions_biz_type"), "wallet_transactions", ["biz_type"], unique=False)
    op.create_index(op.f("ix_wallet_transactions_created_at"), "wallet_transactions", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_wallet_transactions_created_at"), table_name="wallet_transactions")
    op.drop_index(op.f("ix_wallet_transactions_biz_type"), table_name="wallet_transactions")
    op.drop_index(op.f("ix_wallet_transactions_user_pk"), table_name="wallet_transactions")
    op.drop_table("wallet_transactions")
