"""create sys_config table for runtime recommendation tuning

Revision ID: 2026031502
Revises: 2026031501
Create Date: 2026-03-15 23:15:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026031502"
down_revision: str | None = "2026031501"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sys_config",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("config_key", sa.String(length=128), nullable=False),
        sa.Column("config_value", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("config_group", sa.String(length=64), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_sys_config_config_key", "sys_config", ["config_key"], unique=True)
    op.create_index("idx_sys_config_config_group", "sys_config", ["config_group"], unique=False)

    sys_config_table = sa.table(
        "sys_config",
        sa.column("config_key", sa.String(length=128)),
        sa.column("config_value", sa.String(length=255)),
        sa.column("config_group", sa.String(length=64)),
        sa.column("description", sa.Text()),
    )

    op.bulk_insert(
        sys_config_table,
        [
            {
                "config_key": "network.reco.impression_1d_hide_count",
                "config_value": "5",
                "config_group": "network_reco",
                "description": "Hide candidate when impressions in 1 day >= threshold",
            },
            {
                "config_key": "network.reco.penalty.dismiss_base_per_count",
                "config_value": "0.22",
                "config_group": "network_reco",
                "description": "Base dismiss penalty per count in 30 days",
            },
            {
                "config_key": "network.reco.penalty.dismiss_base_cap",
                "config_value": "0.45",
                "config_group": "network_reco",
                "description": "Base dismiss penalty cap",
            },
            {
                "config_key": "network.reco.penalty.dismiss_repeat_per_count",
                "config_value": "0.12",
                "config_group": "network_reco",
                "description": "Extra penalty per dismiss reason=too_many_repeats",
            },
            {
                "config_key": "network.reco.penalty.dismiss_repeat_cap",
                "config_value": "0.24",
                "config_group": "network_reco",
                "description": "Extra penalty cap for reason=too_many_repeats",
            },
            {
                "config_key": "network.reco.penalty.dismiss_mismatch_per_count",
                "config_value": "0.08",
                "config_group": "network_reco",
                "description": "Extra penalty per dismiss reason=industry_mismatch",
            },
            {
                "config_key": "network.reco.penalty.dismiss_mismatch_cap",
                "config_value": "0.16",
                "config_group": "network_reco",
                "description": "Extra penalty cap for reason=industry_mismatch",
            },
            {
                "config_key": "network.reco.penalty.dismiss_not_local_per_count",
                "config_value": "0.08",
                "config_group": "network_reco",
                "description": "Extra penalty per dismiss reason=not_local",
            },
            {
                "config_key": "network.reco.penalty.dismiss_not_local_cap",
                "config_value": "0.16",
                "config_group": "network_reco",
                "description": "Extra penalty cap for reason=not_local",
            },
            {
                "config_key": "network.reco.penalty.exposure_per_count",
                "config_value": "0.08",
                "config_group": "network_reco",
                "description": "Exposure penalty per impression count in 7 days",
            },
            {
                "config_key": "network.reco.penalty.exposure_cap",
                "config_value": "0.35",
                "config_group": "network_reco",
                "description": "Exposure penalty cap",
            },
            {
                "config_key": "network.reco.boost.positive_per_count",
                "config_value": "0.05",
                "config_group": "network_reco",
                "description": "Positive feedback boost per count in 30 days",
            },
            {
                "config_key": "network.reco.boost.positive_cap",
                "config_value": "0.18",
                "config_group": "network_reco",
                "description": "Positive boost cap",
            },
        ],
    )


def downgrade() -> None:
    op.drop_index("idx_sys_config_config_group", table_name="sys_config")
    op.drop_index("idx_sys_config_config_key", table_name="sys_config")
    op.drop_table("sys_config")
