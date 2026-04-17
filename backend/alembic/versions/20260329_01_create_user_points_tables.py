"""create user points tables

Revision ID: 2026032901
Revises: 2026032602
Create Date: 2026-03-29 01:10:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026032901"
down_revision: str | None = "2026032602"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("inviter_user_pk", sa.Integer(), nullable=True))
    op.create_index("ix_users_inviter_user_pk", "users", ["inviter_user_pk"], unique=False)
    op.create_foreign_key(
        "fk_users_inviter_user_pk_users",
        "users",
        "users",
        ["inviter_user_pk"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "user_points_accounts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_pk", sa.Integer(), nullable=False),
        sa.Column("balance", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("frozen_balance", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_pk", name="uq_user_points_accounts_user_pk"),
    )
    op.create_index("ix_user_points_accounts_user_pk", "user_points_accounts", ["user_pk"], unique=True)

    op.create_table(
        "user_points_transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_pk", sa.Integer(), nullable=False),
        sa.Column("change_amount", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("biz_type", sa.String(length=64), nullable=False),
        sa.Column("biz_key", sa.String(length=128), nullable=False, server_default=sa.text("''")),
        sa.Column("title", sa.String(length=64), nullable=False, server_default=sa.text("''")),
        sa.Column("remark", sa.String(length=255), nullable=True),
        sa.Column("meta_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_pk", "biz_type", "biz_key", name="uq_user_points_transactions_user_biz"),
    )
    op.create_index("ix_user_points_transactions_user_pk", "user_points_transactions", ["user_pk"], unique=False)
    op.create_index("ix_user_points_transactions_biz_type", "user_points_transactions", ["biz_type"], unique=False)
    op.create_index("ix_user_points_transactions_created_at", "user_points_transactions", ["created_at"], unique=False)

    op.execute(
        """
        INSERT INTO user_points_accounts (user_pk, balance, frozen_balance, created_at, updated_at)
        SELECT users.id, 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        FROM users
        LEFT JOIN user_points_accounts ON user_points_accounts.user_pk = users.id
        WHERE user_points_accounts.user_pk IS NULL
        """
    )

    op.add_column(
        "member_orders",
        sa.Column("original_amount", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0.00")),
    )
    op.add_column(
        "member_orders",
        sa.Column("points_cost", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "member_orders",
        sa.Column("points_discount_rate", sa.Numeric(6, 4), nullable=False, server_default=sa.text("1.0000")),
    )
    op.add_column(
        "member_orders",
        sa.Column("used_points_discount", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "member_orders",
        sa.Column("points_status", sa.String(length=16), nullable=False, server_default=sa.text("'none'")),
    )

    op.execute(
        """
        UPDATE member_orders
        SET
          original_amount = amount,
          points_cost = 0,
          points_discount_rate = 1.0000,
          used_points_discount = 0,
          points_status = 'none'
        """
    )


def downgrade() -> None:
    op.drop_column("member_orders", "points_status")
    op.drop_column("member_orders", "used_points_discount")
    op.drop_column("member_orders", "points_discount_rate")
    op.drop_column("member_orders", "points_cost")
    op.drop_column("member_orders", "original_amount")

    op.drop_index("ix_user_points_transactions_created_at", table_name="user_points_transactions")
    op.drop_index("ix_user_points_transactions_biz_type", table_name="user_points_transactions")
    op.drop_index("ix_user_points_transactions_user_pk", table_name="user_points_transactions")
    op.drop_table("user_points_transactions")

    op.drop_index("ix_user_points_accounts_user_pk", table_name="user_points_accounts")
    op.drop_table("user_points_accounts")

    op.drop_constraint("fk_users_inviter_user_pk_users", "users", type_="foreignkey")
    op.drop_index("ix_users_inviter_user_pk", table_name="users")
    op.drop_column("users", "inviter_user_pk")
