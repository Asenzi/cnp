"""create member tables

Revision ID: 2026031901
Revises: 2026031802
Create Date: 2026-03-19 16:40:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026031901"
down_revision: str | None = "2026031802"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_memberships",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_pk", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.String(length=32), nullable=False),
        sa.Column("plan_name", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'active'")),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("expire_at", sa.DateTime(), nullable=False),
        sa.Column("last_order_no", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_pk"),
    )
    op.create_index("ix_user_memberships_user_pk", "user_memberships", ["user_pk"], unique=True)
    op.create_index("ix_user_memberships_status", "user_memberships", ["status"], unique=False)
    op.create_index("ix_user_memberships_expire_at", "user_memberships", ["expire_at"], unique=False)

    op.create_table(
        "member_orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("order_no", sa.String(length=32), nullable=False),
        sa.Column("user_pk", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.String(length=32), nullable=False),
        sa.Column("plan_name", sa.String(length=64), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False, server_default=sa.text("30")),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False, server_default=sa.text("0.00")),
        sa.Column("pay_channel", sa.String(length=16), nullable=False, server_default=sa.text("'wallet'")),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'paid'")),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_member_orders_order_no", "member_orders", ["order_no"], unique=True)
    op.create_index("ix_member_orders_user_pk", "member_orders", ["user_pk"], unique=False)
    op.create_index("ix_member_orders_status", "member_orders", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_member_orders_status", table_name="member_orders")
    op.drop_index("ix_member_orders_user_pk", table_name="member_orders")
    op.drop_index("ix_member_orders_order_no", table_name="member_orders")
    op.drop_table("member_orders")

    op.drop_index("ix_user_memberships_expire_at", table_name="user_memberships")
    op.drop_index("ix_user_memberships_status", table_name="user_memberships")
    op.drop_index("ix_user_memberships_user_pk", table_name="user_memberships")
    op.drop_table("user_memberships")
