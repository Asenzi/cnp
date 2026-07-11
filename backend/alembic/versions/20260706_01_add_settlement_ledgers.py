"""add settlement ledgers

Revision ID: 20260706_01
Revises: 20260703_01
Create Date: 2026-07-06 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260706_01"
down_revision = "20260703_01"
branch_labels = None
depends_on = None


def _has_table(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if _has_table(inspector, "settlement_ledgers"):
        return
    op.create_table(
        "settlement_ledgers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_pk", sa.Integer(), nullable=False),
        sa.Column("change_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("available_after", sa.Numeric(12, 2), server_default=sa.text("0.00"), nullable=False),
        sa.Column("frozen_after", sa.Numeric(12, 2), server_default=sa.text("0.00"), nullable=False),
        sa.Column("biz_type", sa.String(length=64), nullable=False),
        sa.Column("biz_key", sa.String(length=128), server_default=sa.text("''"), nullable=False),
        sa.Column("title", sa.String(length=128), server_default=sa.text("''"), nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_pk", "biz_type", "biz_key", name="uq_settlement_ledgers_user_biz"),
    )
    op.create_index(op.f("ix_settlement_ledgers_biz_type"), "settlement_ledgers", ["biz_type"], unique=False)
    op.create_index(op.f("ix_settlement_ledgers_created_at"), "settlement_ledgers", ["created_at"], unique=False)
    op.create_index(op.f("ix_settlement_ledgers_user_pk"), "settlement_ledgers", ["user_pk"], unique=False)


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if _has_table(inspector, "settlement_ledgers"):
        op.drop_table("settlement_ledgers")
