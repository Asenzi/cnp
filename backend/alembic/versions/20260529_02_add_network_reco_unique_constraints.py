"""add network reco unique constraints

Revision ID: 20260529_02
Revises: 20260529_01
Create Date: 2026-05-29

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "20260529_02"
down_revision = "20260529_01"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        DELETE nri1
        FROM network_reco_impressions AS nri1
        INNER JOIN network_reco_impressions AS nri2
            ON nri1.viewer_user_pk = nri2.viewer_user_pk
            AND nri1.target_user_pk = nri2.target_user_pk
            AND nri1.scene = nri2.scene
            AND nri1.tab_key = nri2.tab_key
            AND nri1.request_id = nri2.request_id
            AND nri1.id > nri2.id
        WHERE nri1.request_id IS NOT NULL
          AND nri2.request_id IS NOT NULL
        """
    )
    op.execute(
        """
        DELETE nrf1
        FROM network_reco_feedback AS nrf1
        INNER JOIN network_reco_feedback AS nrf2
            ON nrf1.viewer_user_pk = nrf2.viewer_user_pk
            AND nrf1.target_user_pk = nrf2.target_user_pk
            AND nrf1.scene = nrf2.scene
            AND nrf1.tab_key = nrf2.tab_key
            AND nrf1.request_id = nrf2.request_id
            AND nrf1.event_type = nrf2.event_type
            AND nrf1.id > nrf2.id
        WHERE nrf1.request_id IS NOT NULL
          AND nrf2.request_id IS NOT NULL
        """
    )

    op.create_unique_constraint(
        "uq_network_reco_impressions_request_target",
        "network_reco_impressions",
        ["viewer_user_pk", "target_user_pk", "scene", "tab_key", "request_id"],
    )
    op.create_unique_constraint(
        "uq_network_reco_feedback_request_target_event",
        "network_reco_feedback",
        ["viewer_user_pk", "target_user_pk", "scene", "tab_key", "request_id", "event_type"],
    )


def downgrade():
    op.drop_constraint(
        "uq_network_reco_feedback_request_target_event",
        "network_reco_feedback",
        type_="unique",
    )
    op.drop_constraint(
        "uq_network_reco_impressions_request_target",
        "network_reco_impressions",
        type_="unique",
    )
