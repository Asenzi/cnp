"""add product safety user fields

Revision ID: 20260709_01
Revises: 20260706_01
Create Date: 2026-07-09 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260709_01"
down_revision = "20260706_01"
branch_labels = None
depends_on = None


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _add_column_if_missing(inspector, column_name: str, column) -> None:
    if not _has_column(inspector, "users", column_name):
        op.add_column("users", column)


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    _add_column_if_missing(inspector, "avatar_candidate_url", sa.Column("avatar_candidate_url", sa.String(length=255), nullable=True))
    _add_column_if_missing(inspector, "avatar_review_status", sa.Column("avatar_review_status", sa.String(length=16), server_default=sa.text("'pending'"), nullable=False))
    _add_column_if_missing(inspector, "avatar_reviewed_at", sa.Column("avatar_reviewed_at", sa.DateTime(), nullable=True))
    _add_column_if_missing(inspector, "nickname_candidate", sa.Column("nickname_candidate", sa.String(length=64), nullable=True))
    _add_column_if_missing(inspector, "nickname_review_status", sa.Column("nickname_review_status", sa.String(length=16), server_default=sa.text("'approved'"), nullable=False))
    _add_column_if_missing(inspector, "nickname_reviewed_at", sa.Column("nickname_reviewed_at", sa.DateTime(), nullable=True))
    _add_column_if_missing(inspector, "intro_candidate", sa.Column("intro_candidate", sa.String(length=255), nullable=True))
    _add_column_if_missing(inspector, "intro_review_status", sa.Column("intro_review_status", sa.String(length=16), server_default=sa.text("'approved'"), nullable=False))
    _add_column_if_missing(inspector, "intro_reviewed_at", sa.Column("intro_reviewed_at", sa.DateTime(), nullable=True))
    _add_column_if_missing(inspector, "risk_level", sa.Column("risk_level", sa.String(length=8), server_default=sa.text("'L0'"), nullable=False))
    _add_column_if_missing(inspector, "profile_edit_blocked_until", sa.Column("profile_edit_blocked_until", sa.DateTime(), nullable=True))
    _add_column_if_missing(inspector, "muted_until", sa.Column("muted_until", sa.DateTime(), nullable=True))
    _add_column_if_missing(inspector, "banned_at", sa.Column("banned_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    # ponytail: keep downgrade non-destructive; remove columns manually only after data export.
    pass
