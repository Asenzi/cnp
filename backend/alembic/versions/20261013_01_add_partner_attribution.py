"""add partner attribution and city hierarchy

Revision ID: 20261013_01
Revises: 20261012_01
Create Date: 2026-10-13 00:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20261013_01"
down_revision = "20261012_01"
branch_labels = None
depends_on = None


def _columns(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    if table_name not in inspector.get_table_names():
        return set()
    return {column["name"] for column in inspector.get_columns(table_name)}


def _indexes(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    if table_name not in inspector.get_table_names():
        return set()
    return {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    user_columns = _columns("users")
    if user_columns:
        if "partner_invite_code" not in user_columns:
            op.add_column("users", sa.Column("partner_invite_code", sa.String(length=4), nullable=True))
        if "partner_city_key" not in user_columns:
            op.add_column("users", sa.Column("partner_city_key", sa.String(length=64), nullable=True))
        if "city_partner_user_pk" not in user_columns:
            op.add_column(
                "users",
                sa.Column("city_partner_user_pk", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            )
        indexes = _indexes("users")
        if "ix_users_partner_invite_code" not in indexes:
            op.create_index("ix_users_partner_invite_code", "users", ["partner_invite_code"], unique=True)
        if "ix_users_partner_city_key" not in indexes:
            op.create_index("ix_users_partner_city_key", "users", ["partner_city_key"], unique=True)
        if "ix_users_city_partner_user_pk" not in indexes:
            op.create_index("ix_users_city_partner_user_pk", "users", ["city_partner_user_pk"], unique=False)

    order_columns = _columns("member_orders")
    if order_columns and "referral_partner_user_pk" not in order_columns:
        op.add_column(
            "member_orders",
            sa.Column(
                "referral_partner_user_pk",
                sa.Integer(),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )
    if order_columns and "referral_captured" not in order_columns:
        op.add_column(
            "member_orders",
            sa.Column("referral_captured", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        )
    if order_columns and "ix_member_orders_referral_partner_user_pk" not in _indexes("member_orders"):
        op.create_index(
            "ix_member_orders_referral_partner_user_pk",
            "member_orders",
            ["referral_partner_user_pk"],
            unique=False,
        )


def downgrade() -> None:
    if "referral_captured" in _columns("member_orders"):
        op.drop_column("member_orders", "referral_captured")
    if "referral_partner_user_pk" in _columns("member_orders"):
        if "ix_member_orders_referral_partner_user_pk" in _indexes("member_orders"):
            op.drop_index("ix_member_orders_referral_partner_user_pk", table_name="member_orders")
        op.drop_column("member_orders", "referral_partner_user_pk")
    user_columns = _columns("users")
    for column, index in (
        ("city_partner_user_pk", "ix_users_city_partner_user_pk"),
        ("partner_city_key", "ix_users_partner_city_key"),
        ("partner_invite_code", "ix_users_partner_invite_code"),
    ):
        if column in user_columns:
            if index in _indexes("users"):
                op.drop_index(index, table_name="users")
            op.drop_column("users", column)
