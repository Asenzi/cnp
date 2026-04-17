"""create content reviews table

Revision ID: 2026032601
Revises: 2026032501
Create Date: 2026-03-26 03:10:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026032601"
down_revision: str | None = "2026032501"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "content_reviews",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("review_type", sa.String(length=32), nullable=False),
        sa.Column("action_type", sa.String(length=16), nullable=False, server_default="update"),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("submitter_user_pk", sa.Integer(), nullable=False),
        sa.Column("target_user_pk", sa.Integer(), nullable=True),
        sa.Column("target_circle_code", sa.String(length=16), nullable=True),
        sa.Column("target_post_code", sa.String(length=16), nullable=True),
        sa.Column("review_fee_amount", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("fee_paid", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("trigger_reason", sa.String(length=32), nullable=True),
        sa.Column("risk_tags_json", sa.Text(), nullable=True),
        sa.Column("submit_payload_json", sa.Text(), nullable=True),
        sa.Column("current_payload_json", sa.Text(), nullable=True),
        sa.Column("reject_reason", sa.String(length=255), nullable=True),
        sa.Column("reviewed_by_admin_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["reviewed_by_admin_id"], ["admin_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["submitter_user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_content_reviews_created_at"), "content_reviews", ["created_at"], unique=False)
    op.create_index(op.f("ix_content_reviews_review_type"), "content_reviews", ["review_type"], unique=False)
    op.create_index(op.f("ix_content_reviews_status"), "content_reviews", ["status"], unique=False)
    op.create_index(op.f("ix_content_reviews_submitter_user_pk"), "content_reviews", ["submitter_user_pk"], unique=False)
    op.create_index(op.f("ix_content_reviews_target_circle_code"), "content_reviews", ["target_circle_code"], unique=False)
    op.create_index(op.f("ix_content_reviews_target_post_code"), "content_reviews", ["target_post_code"], unique=False)
    op.create_index(op.f("ix_content_reviews_target_user_pk"), "content_reviews", ["target_user_pk"], unique=False)
    op.create_index(op.f("ix_content_reviews_reviewed_by_admin_id"), "content_reviews", ["reviewed_by_admin_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_content_reviews_reviewed_by_admin_id"), table_name="content_reviews")
    op.drop_index(op.f("ix_content_reviews_target_user_pk"), table_name="content_reviews")
    op.drop_index(op.f("ix_content_reviews_target_post_code"), table_name="content_reviews")
    op.drop_index(op.f("ix_content_reviews_target_circle_code"), table_name="content_reviews")
    op.drop_index(op.f("ix_content_reviews_submitter_user_pk"), table_name="content_reviews")
    op.drop_index(op.f("ix_content_reviews_status"), table_name="content_reviews")
    op.drop_index(op.f("ix_content_reviews_review_type"), table_name="content_reviews")
    op.drop_index(op.f("ix_content_reviews_created_at"), table_name="content_reviews")
    op.drop_table("content_reviews")
