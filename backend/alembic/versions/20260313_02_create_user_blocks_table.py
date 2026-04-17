"""create user blocks table

Revision ID: 2026031302
Revises: 2026031301
Create Date: 2026-03-13 10:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026031302"
down_revision: str | None = "2026031301"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_blocks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_pk", sa.Integer(), nullable=False),
        sa.Column("blocked_user_pk", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["blocked_user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_pk", "blocked_user_pk", name="uq_user_blocks_user_blocked"),
    )
    op.create_index("ix_user_blocks_user_pk", "user_blocks", ["user_pk"], unique=False)
    op.create_index("ix_user_blocks_blocked_user_pk", "user_blocks", ["blocked_user_pk"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_user_blocks_blocked_user_pk", table_name="user_blocks")
    op.drop_index("ix_user_blocks_user_pk", table_name="user_blocks")
    op.drop_table("user_blocks")
