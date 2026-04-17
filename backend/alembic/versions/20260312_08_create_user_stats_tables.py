"""create user stats tables

Revision ID: 2026031208
Revises: 2026031207
Create Date: 2026-03-12 22:05:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026031208"
down_revision: str | None = "2026031207"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_circle_memberships",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_pk", sa.Integer(), nullable=False),
        sa.Column("circle_code", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_pk", "circle_code", name="uq_user_circle_memberships_user_circle"),
    )
    op.create_index(
        "ix_user_circle_memberships_user_pk",
        "user_circle_memberships",
        ["user_pk"],
        unique=False,
    )

    op.create_table(
        "user_connections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_pk", sa.Integer(), nullable=False),
        sa.Column("target_user_pk", sa.Integer(), nullable=True),
        sa.Column("target_name", sa.String(length=64), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["target_user_pk"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_connections_user_pk", "user_connections", ["user_pk"], unique=False)
    op.create_index(
        "ix_user_connections_target_user_pk",
        "user_connections",
        ["target_user_pk"],
        unique=False,
    )

    op.create_table(
        "user_wallets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_pk", sa.Integer(), nullable=False),
        sa.Column("balance", sa.Numeric(12, 2), nullable=False, server_default=sa.text("0.00")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_pk", name="uq_user_wallets_user_pk"),
    )
    op.create_index("ix_user_wallets_user_pk", "user_wallets", ["user_pk"], unique=True)

    op.execute(
        """
        INSERT INTO user_wallets (user_pk, balance, created_at, updated_at)
        SELECT users.id, users.balance, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        FROM users
        LEFT JOIN user_wallets ON user_wallets.user_pk = users.id
        WHERE user_wallets.user_pk IS NULL
        """
    )


def downgrade() -> None:
    op.drop_index("ix_user_wallets_user_pk", table_name="user_wallets")
    op.drop_table("user_wallets")

    op.drop_index("ix_user_connections_target_user_pk", table_name="user_connections")
    op.drop_index("ix_user_connections_user_pk", table_name="user_connections")
    op.drop_table("user_connections")

    op.drop_index("ix_user_circle_memberships_user_pk", table_name="user_circle_memberships")
    op.drop_table("user_circle_memberships")
