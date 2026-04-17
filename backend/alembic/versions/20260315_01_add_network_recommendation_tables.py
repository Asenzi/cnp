"""add network recommendation tables and user city fields

Revision ID: 2026031501
Revises: 2026031304
Create Date: 2026-03-15 14:20:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026031501"
down_revision: str | None = "2026031304"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("city_code", sa.String(length=16), nullable=True))
    op.add_column("users", sa.Column("city_name", sa.String(length=32), nullable=True))
    op.create_index("idx_users_city_code", "users", ["city_code"], unique=False)

    op.create_table(
        "network_reco_impressions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("viewer_user_pk", sa.Integer(), nullable=False),
        sa.Column("target_user_pk", sa.Integer(), nullable=False),
        sa.Column("scene", sa.String(length=16), nullable=False),
        sa.Column("tab_key", sa.String(length=16), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["target_user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["viewer_user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_network_reco_impressions_viewer_user_pk",
        "network_reco_impressions",
        ["viewer_user_pk"],
        unique=False,
    )
    op.create_index(
        "idx_network_reco_impressions_target_user_pk",
        "network_reco_impressions",
        ["target_user_pk"],
        unique=False,
    )
    op.create_index(
        "idx_network_reco_impressions_created_at",
        "network_reco_impressions",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "idx_network_reco_impressions_request_id",
        "network_reco_impressions",
        ["request_id"],
        unique=False,
    )

    op.create_table(
        "network_reco_feedback",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("viewer_user_pk", sa.Integer(), nullable=False),
        sa.Column("target_user_pk", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=24), nullable=False),
        sa.Column("scene", sa.String(length=16), nullable=False),
        sa.Column("tab_key", sa.String(length=16), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("ext_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["target_user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["viewer_user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_network_reco_feedback_viewer_user_pk",
        "network_reco_feedback",
        ["viewer_user_pk"],
        unique=False,
    )
    op.create_index(
        "idx_network_reco_feedback_target_user_pk",
        "network_reco_feedback",
        ["target_user_pk"],
        unique=False,
    )
    op.create_index(
        "idx_network_reco_feedback_event_type",
        "network_reco_feedback",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        "idx_network_reco_feedback_created_at",
        "network_reco_feedback",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_network_reco_feedback_created_at", table_name="network_reco_feedback")
    op.drop_index("idx_network_reco_feedback_event_type", table_name="network_reco_feedback")
    op.drop_index("idx_network_reco_feedback_target_user_pk", table_name="network_reco_feedback")
    op.drop_index("idx_network_reco_feedback_viewer_user_pk", table_name="network_reco_feedback")
    op.drop_table("network_reco_feedback")

    op.drop_index("idx_network_reco_impressions_request_id", table_name="network_reco_impressions")
    op.drop_index("idx_network_reco_impressions_created_at", table_name="network_reco_impressions")
    op.drop_index("idx_network_reco_impressions_target_user_pk", table_name="network_reco_impressions")
    op.drop_index("idx_network_reco_impressions_viewer_user_pk", table_name="network_reco_impressions")
    op.drop_table("network_reco_impressions")

    op.drop_index("idx_users_city_code", table_name="users")
    op.drop_column("users", "city_name")
    op.drop_column("users", "city_code")
