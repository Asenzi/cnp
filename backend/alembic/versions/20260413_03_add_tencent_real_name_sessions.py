"""add tencent real-name verification sessions

Revision ID: 2026041303
Revises: 2026041302
Create Date: 2026-04-13 15:10:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026041303"
down_revision: str | None = "2026041302"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "user_real_name_profiles",
        sa.Column("verification_provider", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "user_real_name_profiles",
        sa.Column("provider_biz_token", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "user_real_name_profiles",
        sa.Column("provider_request_id", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "user_real_name_profiles",
        sa.Column("provider_result_json", sa.Text(), nullable=True),
    )
    op.add_column(
        "user_real_name_profiles",
        sa.Column("verified_source", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "user_real_name_profiles",
        sa.Column("last_verified_at", sa.DateTime(), nullable=True),
    )
    op.drop_index("ix_user_real_name_profiles_id_number_hash", table_name="user_real_name_profiles")
    op.create_unique_constraint(
        "uq_user_real_name_profiles_id_number_hash",
        "user_real_name_profiles",
        ["id_number_hash"],
    )

    op.create_table(
        "user_real_name_verification_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_pk", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_biz_token", sa.String(length=128), nullable=False),
        sa.Column("provider_request_id", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("real_name", sa.String(length=32), nullable=False),
        sa.Column("id_number_masked", sa.String(length=32), nullable=False),
        sa.Column("id_number_hash", sa.String(length=64), nullable=False),
        sa.Column("redirect_url", sa.String(length=255), nullable=True),
        sa.Column("fail_reason", sa.String(length=255), nullable=True),
        sa.Column("request_payload_json", sa.Text(), nullable=True),
        sa.Column("result_payload_json", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_user_real_name_verify_sessions_user_status",
        "user_real_name_verification_sessions",
        ["user_pk", "status"],
        unique=False,
    )
    op.create_index(
        "ix_user_real_name_verify_sessions_id_hash",
        "user_real_name_verification_sessions",
        ["id_number_hash"],
        unique=False,
    )
    op.create_index(
        "ix_user_real_name_verify_sessions_provider_biz_token",
        "user_real_name_verification_sessions",
        ["provider_biz_token"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_user_real_name_verify_sessions_provider_biz_token",
        table_name="user_real_name_verification_sessions",
    )
    op.drop_index(
        "ix_user_real_name_verify_sessions_id_hash",
        table_name="user_real_name_verification_sessions",
    )
    op.drop_index(
        "ix_user_real_name_verify_sessions_user_status",
        table_name="user_real_name_verification_sessions",
    )
    op.drop_table("user_real_name_verification_sessions")

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
    op.drop_column("user_real_name_profiles", "last_verified_at")
    op.drop_column("user_real_name_profiles", "verified_source")
    op.drop_column("user_real_name_profiles", "provider_result_json")
    op.drop_column("user_real_name_profiles", "provider_request_id")
    op.drop_column("user_real_name_profiles", "provider_biz_token")
    op.drop_column("user_real_name_profiles", "verification_provider")
