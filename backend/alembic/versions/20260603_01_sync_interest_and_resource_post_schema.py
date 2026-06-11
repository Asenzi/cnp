"""sync interest tables and resource post venue columns

Revision ID: 20260603_01
Revises: 20260602_03
Create Date: 2026-06-03 13:36:00

"""
from alembic import op
import sqlalchemy as sa


revision = "20260603_01"
down_revision = "20260602_03"
branch_labels = None
depends_on = None


def _table_exists(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in set(inspector.get_table_names())


def _column_exists(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    if not _table_exists(inspector, table_name):
        return False
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _index_exists(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    if not _table_exists(inspector, table_name):
        return False
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _table_exists(inspector, "user_interests"):
        op.create_table(
            "user_interests",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_pk", sa.Integer(), nullable=False),
            sa.Column("target_user_pk", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["user_pk"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["target_user_pk"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_pk", "target_user_pk", name="uq_user_interest"),
        )
        inspector = sa.inspect(bind)
    if not _index_exists(inspector, "user_interests", "ix_user_interests_user_pk"):
        op.create_index("ix_user_interests_user_pk", "user_interests", ["user_pk"], unique=False)
    if not _index_exists(inspector, "user_interests", "ix_user_interests_target_user_pk"):
        op.create_index("ix_user_interests_target_user_pk", "user_interests", ["target_user_pk"], unique=False)

    inspector = sa.inspect(bind)
    if not _table_exists(inspector, "circle_interests"):
        op.create_table(
            "circle_interests",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_pk", sa.Integer(), nullable=False),
            sa.Column("circle_pk", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.ForeignKeyConstraint(["user_pk"], ["users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["circle_pk"], ["circles.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_pk", "circle_pk", name="uq_circle_interest"),
        )
        inspector = sa.inspect(bind)
    if not _index_exists(inspector, "circle_interests", "ix_circle_interests_user_pk"):
        op.create_index("ix_circle_interests_user_pk", "circle_interests", ["user_pk"], unique=False)
    if not _index_exists(inspector, "circle_interests", "ix_circle_interests_circle_pk"):
        op.create_index("ix_circle_interests_circle_pk", "circle_interests", ["circle_pk"], unique=False)

    inspector = sa.inspect(bind)
    resource_post_columns = [
        ("event_date", sa.Column("event_date", sa.String(length=32), nullable=True)),
        ("event_time", sa.Column("event_time", sa.String(length=32), nullable=True)),
        ("duration", sa.Column("duration", sa.Integer(), nullable=True)),
        ("capacity", sa.Column("capacity", sa.Integer(), nullable=True)),
        ("location", sa.Column("location", sa.String(length=255), nullable=True)),
        ("address", sa.Column("address", sa.Text(), nullable=True)),
        ("payment_type", sa.Column("payment_type", sa.String(length=16), nullable=True)),
        ("price", sa.Column("price", sa.String(length=32), nullable=True)),
        ("contact", sa.Column("contact", sa.String(length=64), nullable=True)),
        ("detail_content", sa.Column("detail_content", sa.Text(), nullable=True)),
        ("participant_count", sa.Column("participant_count", sa.Integer(), nullable=False, server_default=sa.text("0"))),
    ]
    for column_name, column in resource_post_columns:
        if not _column_exists(inspector, "resource_posts", column_name):
            op.add_column("resource_posts", column)
            inspector = sa.inspect(bind)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for column_name in [
        "participant_count",
        "detail_content",
        "contact",
        "price",
        "payment_type",
        "address",
        "location",
        "capacity",
        "duration",
        "event_time",
        "event_date",
    ]:
        if _column_exists(inspector, "resource_posts", column_name):
            op.drop_column("resource_posts", column_name)
            inspector = sa.inspect(bind)

    if _table_exists(inspector, "circle_interests"):
        op.drop_table("circle_interests")
        inspector = sa.inspect(bind)
    if _table_exists(inspector, "user_interests"):
        op.drop_table("user_interests")
