"""
验证数据库迁移结果
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.core.database import engine


def verify_migration():
    """验证迁移结果"""
    print("=" * 60)
    print("Verifying migration results...")
    print("=" * 60)

    with engine.connect() as conn:
        # 检查表是否存在
        result = conn.execute(text("SHOW TABLES LIKE 'user_interests'"))
        tables = result.fetchall()

        if not tables:
            print("[ERROR] Table 'user_interests' not found!")
            return False

        print("[OK] Table 'user_interests' exists")

        # 查看表结构
        print("\nTable structure:")
        result = conn.execute(text("DESCRIBE user_interests"))
        for row in result:
            print(f"  {row[0]:20} {row[1]:20} {row[2]:10} {row[3]:10}")

        # 查看索引
        print("\nIndexes:")
        result = conn.execute(text("SHOW INDEX FROM user_interests"))
        for row in result:
            print(f"  {row[2]:40} Column: {row[4]:20} Unique: {row[1] == 0}")

        print("\n" + "=" * 60)
        print("[SUCCESS] Migration verified successfully!")
        print("=" * 60)
        return True


if __name__ == "__main__":
    success = verify_migration()
    sys.exit(0 if success else 1)
