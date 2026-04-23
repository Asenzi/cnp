"""create user contact package balances

Revision ID: 20260421_01
Revises: 20260415_01
Create Date: 2026-04-21 11:10:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260421_01"
down_revision: str | None = "20260415_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_contact_package_balances",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_pk", sa.Integer(), nullable=False),
        sa.Column("purchased_views", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("used_views", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("remaining_views", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_order_no", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_pk", name="uq_user_contact_package_balances_user_pk"),
    )
    op.create_index(
        "ix_user_contact_package_balances_user_pk",
        "user_contact_package_balances",
        ["user_pk"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_user_contact_package_balances_user_pk", table_name="user_contact_package_balances")
    op.drop_table("user_contact_package_balances")
