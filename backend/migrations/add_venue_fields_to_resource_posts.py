"""
添加活动相关字段到 resource_posts 表

运行方式：
python migrations/add_venue_fields_to_resource_posts.py
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text

from app.core.database import engine


def upgrade():
    """添加活动相关字段"""
    with engine.connect() as conn:
        # 添加活动相关字段，逐个添加以避免语法错误
        fields = [
            ("event_date", "VARCHAR(32)"),
            ("event_time", "VARCHAR(32)"),
            ("duration", "INTEGER"),
            ("capacity", "INTEGER"),
            ("location", "VARCHAR(255)"),
            ("address", "TEXT"),
            ("payment_type", "VARCHAR(16)"),
            ("price", "VARCHAR(32)"),
            ("contact", "VARCHAR(64)"),
            ("detail_content", "TEXT"),
            ("participant_count", "INTEGER DEFAULT 0 NOT NULL"),
        ]

        for field_name, field_type in fields:
            try:
                conn.execute(text(f"ALTER TABLE resource_posts ADD COLUMN {field_name} {field_type}"))
                conn.commit()
                print(f"[OK] 成功添加字段: {field_name}")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print(f"[SKIP] 字段已存在，跳过: {field_name}")
                else:
                    print(f"[ERROR] 添加字段失败: {field_name}, 错误: {e}")
                    raise

        print("[OK] 所有活动相关字段添加完成")


def downgrade():
    """删除活动相关字段"""
    with engine.connect() as conn:
        fields = [
            "event_date", "event_time", "duration", "capacity", "location",
            "address", "payment_type", "price", "contact", "detail_content", "participant_count"
        ]

        for field_name in fields:
            try:
                conn.execute(text(f"ALTER TABLE resource_posts DROP COLUMN {field_name}"))
                conn.commit()
                print(f"[OK] 成功删除字段: {field_name}")
            except Exception as e:
                if "Can't DROP" in str(e):
                    print(f"[SKIP] 字段不存在，跳过: {field_name}")
                else:
                    print(f"[ERROR] 删除字段失败: {field_name}, 错误: {e}")

        print("[OK] 所有活动相关字段删除完成")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="数据库迁移：添加活动相关字段")
    parser.add_argument(
        "--downgrade",
        action="store_true",
        help="回滚迁移（删除字段）"
    )
    args = parser.parse_args()

    if args.downgrade:
        print("开始回滚迁移...")
        downgrade()
    else:
        print("开始执行迁移...")
        upgrade()
