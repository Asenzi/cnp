"""add wechat binding fields on users

Revision ID: 2026031210
Revises: 2026031209
Create Date: 2026-03-12 23:59:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2026031210"
down_revision: str | None = "2026031209"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("wechat_openid", sa.String(length=64), nullable=True))
    op.add_column("users", sa.Column("wechat_unionid", sa.String(length=64), nullable=True))
    op.add_column("users", sa.Column("wechat_bound_at", sa.DateTime(), nullable=True))
    op.create_index("ix_users_wechat_openid", "users", ["wechat_openid"], unique=True)
    op.create_index("ix_users_wechat_unionid", "users", ["wechat_unionid"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_wechat_unionid", table_name="users")
    op.drop_index("ix_users_wechat_openid", table_name="users")
    op.drop_column("users", "wechat_bound_at")
    op.drop_column("users", "wechat_unionid")
    op.drop_column("users", "wechat_openid")
