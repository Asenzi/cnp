"""create user feedback table

Revision ID: 20260529_01
Revises: 20260428_01
Create Date: 2026-05-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260529_01"
down_revision = "20260428_01"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_feedback",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticket_no", sa.String(length=24), nullable=False),
        sa.Column("user_pk", sa.Integer(), nullable=False),
        sa.Column("feedback_type", sa.String(length=32), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("contact", sa.String(length=100), nullable=True),
        sa.Column("images_json", sa.Text(), nullable=True),
        sa.Column(
            "source_page",
            sa.String(length=64),
            nullable=False,
            server_default=sa.text("'pages/me/help-feedback/index'"),
        ),
        sa.Column(
            "status",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_feedback_created_at", "user_feedback", ["created_at"], unique=False)
    op.create_index("ix_user_feedback_feedback_type", "user_feedback", ["feedback_type"], unique=False)
    op.create_index("ix_user_feedback_status", "user_feedback", ["status"], unique=False)
    op.create_index("ix_user_feedback_ticket_no", "user_feedback", ["ticket_no"], unique=True)
    op.create_index("ix_user_feedback_user_pk", "user_feedback", ["user_pk"], unique=False)


def downgrade():
    op.drop_index("ix_user_feedback_user_pk", table_name="user_feedback")
    op.drop_index("ix_user_feedback_ticket_no", table_name="user_feedback")
    op.drop_index("ix_user_feedback_status", table_name="user_feedback")
    op.drop_index("ix_user_feedback_feedback_type", table_name="user_feedback")
    op.drop_index("ix_user_feedback_created_at", table_name="user_feedback")
    op.drop_table("user_feedback")
