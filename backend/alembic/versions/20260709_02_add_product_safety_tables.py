"""add product safety tables

Revision ID: 20260709_02
Revises: 20260709_01
Create Date: 2026-07-09 00:10:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260709_02"
down_revision = "20260709_01"
branch_labels = None
depends_on = None


def _has_table(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not _has_table(inspector, "product_safety_review_logs"):
        op.create_table(
            "product_safety_review_logs",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_pk", sa.Integer(), nullable=True),
            sa.Column("content_type", sa.String(length=32), nullable=False),
            sa.Column("content_value", sa.Text(), nullable=True),
            sa.Column("provider", sa.String(length=32), nullable=False),
            sa.Column("provider_request_id", sa.String(length=128), nullable=True),
            sa.Column("provider_result", sa.String(length=32), nullable=False),
            sa.Column("risk_labels_json", sa.Text(), nullable=True),
            sa.Column("final_result", sa.String(length=32), nullable=False),
            sa.Column("reject_reason", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["user_pk"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        for column in ("user_pk", "content_type", "provider", "provider_result", "final_result", "created_at"):
            op.create_index(op.f(f"ix_product_safety_review_logs_{column}"), "product_safety_review_logs", [column], unique=False)

    if not _has_table(inspector, "product_safety_punishments"):
        op.create_table(
            "product_safety_punishments",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_pk", sa.Integer(), nullable=False),
            sa.Column("punishment_type", sa.String(length=32), nullable=False),
            sa.Column("reason", sa.String(length=255), nullable=True),
            sa.Column("source", sa.String(length=32), server_default=sa.text("'system'"), nullable=False),
            sa.Column("starts_at", sa.DateTime(), nullable=True),
            sa.Column("ends_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["user_pk"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        for column in ("user_pk", "punishment_type", "created_at"):
            op.create_index(op.f(f"ix_product_safety_punishments_{column}"), "product_safety_punishments", [column], unique=False)

    if not _has_table(inspector, "content_reports"):
        op.create_table(
            "content_reports",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("reporter_user_pk", sa.Integer(), nullable=False),
            sa.Column("target_user_pk", sa.Integer(), nullable=True),
            sa.Column("target_type", sa.String(length=32), nullable=False),
            sa.Column("target_id", sa.String(length=64), nullable=False),
            sa.Column("reason", sa.String(length=255), nullable=True),
            sa.Column("status", sa.String(length=16), server_default=sa.text("'pending'"), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["reporter_user_pk"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["target_user_pk"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        for column in ("reporter_user_pk", "target_user_pk", "target_type", "target_id", "status", "created_at"):
            op.create_index(op.f(f"ix_content_reports_{column}"), "content_reports", [column], unique=False)

    if not _has_table(inspector, "product_safety_retry_tasks"):
        op.create_table(
            "product_safety_retry_tasks",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_pk", sa.Integer(), nullable=True),
            sa.Column("content_type", sa.String(length=32), nullable=False),
            sa.Column("content_value", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=16), server_default=sa.text("'pending'"), nullable=False),
            sa.Column("attempt_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
            sa.Column("next_retry_at", sa.DateTime(), nullable=True),
            sa.Column("last_error", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["user_pk"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        for column in ("user_pk", "content_type", "status", "next_retry_at", "created_at"):
            op.create_index(op.f(f"ix_product_safety_retry_tasks_{column}"), "product_safety_retry_tasks", [column], unique=False)


def downgrade() -> None:
    # ponytail: non-destructive downgrade; drop manually only after exporting safety evidence.
    pass
