"""create user_real_name_profiles table

Revision ID: 2026041302
Revises: 2026041301
Create Date: 2026-04-13 13:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026041302"
down_revision: str | None = "2026041301"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_real_name_profiles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_pk", sa.Integer(), nullable=False),
        sa.Column("real_name", sa.String(length=32), nullable=False),
        sa.Column("id_number_masked", sa.String(length=32), nullable=False),
        sa.Column("id_number_hash", sa.String(length=64), nullable=False),
        sa.Column("id_number_encrypted", sa.Text(), nullable=False),
        sa.Column("id_front_url", sa.String(length=255), nullable=False),
        sa.Column("id_back_url", sa.String(length=255), nullable=False),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_pk"),
    )
    op.create_index(
        "ix_user_real_name_profiles_id_number_hash",
        "user_real_name_profiles",
        ["id_number_hash"],
        unique=False,
    )
    op.create_index(
        "ix_user_real_name_profiles_verified_at",
        "user_real_name_profiles",
        ["verified_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_user_real_name_profiles_verified_at", table_name="user_real_name_profiles")
    op.drop_index("ix_user_real_name_profiles_id_number_hash", table_name="user_real_name_profiles")
    op.drop_table("user_real_name_profiles")
