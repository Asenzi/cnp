"""create user verifications table

Revision ID: 2026031209
Revises: 2026031208
Create Date: 2026-03-12 23:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026031209"
down_revision: str | None = "2026031208"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_verifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_pk", sa.Integer(), nullable=False),
        sa.Column("verify_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("submit_payload_json", sa.Text(), nullable=True),
        sa.Column("reject_reason", sa.String(length=255), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_pk", "verify_type", name="uq_user_verifications_user_type"),
    )
    op.create_index("ix_user_verifications_user_pk", "user_verifications", ["user_pk"], unique=False)
    op.create_index("ix_user_verifications_verify_type", "user_verifications", ["verify_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_user_verifications_verify_type", table_name="user_verifications")
    op.drop_index("ix_user_verifications_user_pk", table_name="user_verifications")
    op.drop_table("user_verifications")
