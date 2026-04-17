"""create resource post circle syncs

Revision ID: 20260415_01
Revises: 2026041303
Create Date: 2026-04-15 01:50:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260415_01"
down_revision = "2026041303"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "resource_post_circle_syncs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("post_pk", sa.Integer(), nullable=False),
        sa.Column("circle_code", sa.String(length=16), nullable=False),
        sa.Column("request_user_pk", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("reviewed_by_user_pk", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("reject_reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["post_pk"], ["resource_posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["request_user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by_user_pk"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("post_pk", "circle_code", name="uq_resource_post_circle_sync_post_circle"),
    )
    op.create_index("ix_resource_post_circle_syncs_post_pk", "resource_post_circle_syncs", ["post_pk"], unique=False)
    op.create_index("ix_resource_post_circle_syncs_circle_code", "resource_post_circle_syncs", ["circle_code"], unique=False)
    op.create_index(
        "ix_resource_post_circle_syncs_request_user_pk",
        "resource_post_circle_syncs",
        ["request_user_pk"],
        unique=False,
    )
    op.create_index("ix_resource_post_circle_syncs_status", "resource_post_circle_syncs", ["status"], unique=False)
    op.create_index(
        "ix_resource_post_circle_syncs_reviewed_by_user_pk",
        "resource_post_circle_syncs",
        ["reviewed_by_user_pk"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_resource_post_circle_syncs_reviewed_by_user_pk", table_name="resource_post_circle_syncs")
    op.drop_index("ix_resource_post_circle_syncs_status", table_name="resource_post_circle_syncs")
    op.drop_index("ix_resource_post_circle_syncs_request_user_pk", table_name="resource_post_circle_syncs")
    op.drop_index("ix_resource_post_circle_syncs_circle_code", table_name="resource_post_circle_syncs")
    op.drop_index("ix_resource_post_circle_syncs_post_pk", table_name="resource_post_circle_syncs")
    op.drop_table("resource_post_circle_syncs")
