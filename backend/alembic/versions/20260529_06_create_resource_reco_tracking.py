"""create resource recommendation tracking tables

Revision ID: 20260529_06
Revises: 20260529_05
Create Date: 2026-06-01

"""
from alembic import op
import sqlalchemy as sa


revision = "20260529_06"
down_revision = "20260529_05"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "resource_post_impressions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("viewer_user_pk", sa.Integer(), nullable=False),
        sa.Column("post_pk", sa.Integer(), nullable=False),
        sa.Column("scene", sa.String(length=16), nullable=False),
        sa.Column("tab_key", sa.String(length=16), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["post_pk"], ["resource_posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["viewer_user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "viewer_user_pk",
            "post_pk",
            "scene",
            "tab_key",
            "request_id",
            name="uq_resource_post_impressions_request_post",
        ),
    )
    op.create_index("ix_resource_post_impressions_viewer_user_pk", "resource_post_impressions", ["viewer_user_pk"])
    op.create_index("ix_resource_post_impressions_post_pk", "resource_post_impressions", ["post_pk"])
    op.create_index("ix_resource_post_impressions_request_id", "resource_post_impressions", ["request_id"])
    op.create_index("ix_resource_post_impressions_created_at", "resource_post_impressions", ["created_at"])

    op.create_table(
        "resource_post_reco_feedback",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("viewer_user_pk", sa.Integer(), nullable=False),
        sa.Column("post_pk", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=24), nullable=False),
        sa.Column("scene", sa.String(length=16), nullable=False),
        sa.Column("tab_key", sa.String(length=16), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("ext_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["post_pk"], ["resource_posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["viewer_user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "viewer_user_pk",
            "post_pk",
            "scene",
            "tab_key",
            "request_id",
            "event_type",
            name="uq_resource_post_reco_feedback_request_event",
        ),
    )
    op.create_index("ix_resource_post_reco_feedback_viewer_user_pk", "resource_post_reco_feedback", ["viewer_user_pk"])
    op.create_index("ix_resource_post_reco_feedback_post_pk", "resource_post_reco_feedback", ["post_pk"])
    op.create_index("ix_resource_post_reco_feedback_event_type", "resource_post_reco_feedback", ["event_type"])
    op.create_index("ix_resource_post_reco_feedback_created_at", "resource_post_reco_feedback", ["created_at"])


def downgrade():
    op.drop_index("ix_resource_post_reco_feedback_created_at", table_name="resource_post_reco_feedback")
    op.drop_index("ix_resource_post_reco_feedback_event_type", table_name="resource_post_reco_feedback")
    op.drop_index("ix_resource_post_reco_feedback_post_pk", table_name="resource_post_reco_feedback")
    op.drop_index("ix_resource_post_reco_feedback_viewer_user_pk", table_name="resource_post_reco_feedback")
    op.drop_table("resource_post_reco_feedback")

    op.drop_index("ix_resource_post_impressions_created_at", table_name="resource_post_impressions")
    op.drop_index("ix_resource_post_impressions_request_id", table_name="resource_post_impressions")
    op.drop_index("ix_resource_post_impressions_post_pk", table_name="resource_post_impressions")
    op.drop_index("ix_resource_post_impressions_viewer_user_pk", table_name="resource_post_impressions")
    op.drop_table("resource_post_impressions")
