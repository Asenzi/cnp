"""create circles table

Revision ID: 2026031303
Revises: 2026031302
Create Date: 2026-03-13 12:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026031303"
down_revision: str | None = "2026031302"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "circles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("circle_code", sa.String(length=16), nullable=False),
        sa.Column("owner_user_pk", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("industry_label", sa.String(length=64), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("cover_url", sa.String(length=255), nullable=False),
        sa.Column("join_type", sa.String(length=16), nullable=False, server_default=sa.text("'free'")),
        sa.Column("join_price", sa.Numeric(precision=10, scale=2), nullable=False, server_default=sa.text("0.00")),
        sa.Column("rules_text", sa.Text(), nullable=True),
        sa.Column("need_post_review", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'active'")),
        sa.Column("member_count", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("post_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("last_active_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["owner_user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_circles_circle_code", "circles", ["circle_code"], unique=True)
    op.create_index("ix_circles_owner_user_pk", "circles", ["owner_user_pk"], unique=False)

    op.create_index("ix_user_circle_memberships_circle_code", "user_circle_memberships", ["circle_code"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_user_circle_memberships_circle_code", table_name="user_circle_memberships")
    op.drop_index("ix_circles_owner_user_pk", table_name="circles")
    op.drop_index("ix_circles_circle_code", table_name="circles")
    op.drop_table("circles")
