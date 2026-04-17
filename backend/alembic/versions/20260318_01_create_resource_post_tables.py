"""create resource post tables

Revision ID: 2026031801
Revises: 2026031701
Create Date: 2026-03-18 23:50:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026031801"
down_revision: str | None = "2026031701"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "resource_posts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("post_code", sa.String(length=16), nullable=False),
        sa.Column("author_user_pk", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(length=16), nullable=False, server_default=sa.text("'cooperate'")),
        sa.Column("industry_label", sa.String(length=64), nullable=True),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("images_json", sa.Text(), nullable=True),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("like_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("comment_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'active'")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["author_user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_resource_posts_post_code", "resource_posts", ["post_code"], unique=True)
    op.create_index("ix_resource_posts_author_user_pk", "resource_posts", ["author_user_pk"], unique=False)
    op.create_index("ix_resource_posts_status", "resource_posts", ["status"], unique=False)
    op.create_index("ix_resource_posts_created_at", "resource_posts", ["created_at"], unique=False)
    op.create_index("ix_resource_posts_mode_status_created", "resource_posts", ["mode", "status", "created_at"], unique=False)

    op.create_table(
        "resource_post_likes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("post_pk", sa.Integer(), nullable=False),
        sa.Column("user_pk", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["post_pk"], ["resource_posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_pk"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("post_pk", "user_pk", name="uq_resource_post_likes_post_user"),
    )
    op.create_index("ix_resource_post_likes_post_pk", "resource_post_likes", ["post_pk"], unique=False)
    op.create_index("ix_resource_post_likes_user_pk", "resource_post_likes", ["user_pk"], unique=False)
    op.create_index("ix_resource_post_likes_created_at", "resource_post_likes", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_resource_post_likes_created_at", table_name="resource_post_likes")
    op.drop_index("ix_resource_post_likes_user_pk", table_name="resource_post_likes")
    op.drop_index("ix_resource_post_likes_post_pk", table_name="resource_post_likes")
    op.drop_table("resource_post_likes")

    op.drop_index("ix_resource_posts_mode_status_created", table_name="resource_posts")
    op.drop_index("ix_resource_posts_created_at", table_name="resource_posts")
    op.drop_index("ix_resource_posts_status", table_name="resource_posts")
    op.drop_index("ix_resource_posts_author_user_pk", table_name="resource_posts")
    op.drop_index("ix_resource_posts_post_code", table_name="resource_posts")
    op.drop_table("resource_posts")
