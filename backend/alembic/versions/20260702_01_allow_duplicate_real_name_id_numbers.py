"""allow duplicate real-name id numbers

Revision ID: 20260702_01
Revises: 20260625_01
Create Date: 2026-07-02 15:30:00
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260702_01"
down_revision: str | None = "20260625_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_user_real_name_profiles_id_number_hash",
        "user_real_name_profiles",
        type_="unique",
    )
    op.create_index(
        "ix_user_real_name_profiles_id_number_hash",
        "user_real_name_profiles",
        ["id_number_hash"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_user_real_name_profiles_id_number_hash",
        table_name="user_real_name_profiles",
    )
    op.create_unique_constraint(
        "uq_user_real_name_profiles_id_number_hash",
        "user_real_name_profiles",
        ["id_number_hash"],
    )
