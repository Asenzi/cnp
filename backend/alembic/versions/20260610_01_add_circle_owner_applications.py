"""add circle owner applications

Revision ID: 20260610_01
Revises: 20260609_01
Create Date: 2026-06-10 20:30:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


revision = "20260610_01"
down_revision = "20260609_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    user_columns = {column["name"] for column in inspector.get_columns("users")}
    if "is_circle_owner" not in user_columns:
        op.add_column(
            "users",
            sa.Column(
                "is_circle_owner",
                sa.Boolean(),
                server_default=sa.text("0"),
                nullable=False,
            ),
        )
        op.create_index(
            "ix_users_is_circle_owner",
            "users",
            ["is_circle_owner"],
            unique=False,
        )

    if "circle_owner_applications" not in set(inspector.get_table_names()):
        op.create_table(
            "circle_owner_applications",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_pk", sa.Integer(), nullable=False),
            sa.Column("reason", sa.String(length=500), nullable=False),
            sa.Column("experience", sa.String(length=500), nullable=True),
            sa.Column(
                "status",
                sa.String(length=16),
                server_default=sa.text("'pending'"),
                nullable=False,
            ),
            sa.Column("reject_reason", sa.String(length=500), nullable=True),
            sa.Column("reviewed_by_admin_id", sa.Integer(), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["user_pk"],
                ["users.id"],
                name="fk_circle_owner_applications_user",
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["reviewed_by_admin_id"],
                ["admin_users.id"],
                name="fk_circle_owner_applications_admin",
                ondelete="SET NULL",
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_pk", name="uq_circle_owner_application_user"),
            mysql_charset="utf8mb4",
            mysql_collate="utf8mb4_unicode_ci",
            mysql_engine="InnoDB",
        )
        op.create_index(
            "ix_circle_owner_applications_user_pk",
            "circle_owner_applications",
            ["user_pk"],
            unique=False,
        )
        op.create_index(
            "ix_circle_owner_applications_status",
            "circle_owner_applications",
            ["status"],
            unique=False,
        )

def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "circle_owner_applications" in set(inspector.get_table_names()):
        op.drop_table("circle_owner_applications")

    user_columns = {column["name"] for column in inspector.get_columns("users")}
    if "is_circle_owner" in user_columns:
        indexes = {item["name"] for item in inspector.get_indexes("users")}
        if "ix_users_is_circle_owner" in indexes:
            op.drop_index("ix_users_is_circle_owner", table_name="users")
        op.drop_column("users", "is_circle_owner")
