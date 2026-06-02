"""create circle join requests table

Revision ID: 20260601_01
Revises: 20260529_06
Create Date: 2026-06-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260601_01"
down_revision = "20260529_06"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "circle_join_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_pk", sa.Integer(), nullable=False),
        sa.Column("circle_code", sa.String(length=32), nullable=False),
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'pending'"),
            comment="pending: 待审核, approved: 已通过, rejected: 已拒绝",
        ),
        sa.Column("message", sa.Text(), nullable=True, comment="申请留言"),
        sa.Column("reject_reason", sa.String(length=255), nullable=True, comment="拒绝原因"),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True, comment="审核时间"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_pk", "circle_code", name="uq_circle_join_requests_user_circle"),
    )
    op.create_index("ix_circle_join_requests_user_pk", "circle_join_requests", ["user_pk"], unique=False)
    op.create_index("ix_circle_join_requests_circle_code", "circle_join_requests", ["circle_code"], unique=False)


def downgrade():
    op.drop_index("ix_circle_join_requests_circle_code", table_name="circle_join_requests")
    op.drop_index("ix_circle_join_requests_user_pk", table_name="circle_join_requests")
    op.drop_table("circle_join_requests")
