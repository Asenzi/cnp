"""
数据库迁移脚本 - 创建 user_interests 表
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.core.database import engine
from app.core.config import settings


def run_migration():
    """执行数据库迁移"""
    print("=" * 60)
    print("Starting database migration: create user_interests table")
    print("=" * 60)
    print(f"Database: {settings.MYSQL_DB}")
    print(f"Host: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}")
    print("-" * 60)

    # 定义 SQL 语句（按顺序执行）
    sql_statements = [
        # 1. 创建表
        """
        CREATE TABLE IF NOT EXISTS user_interests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_pk INT NOT NULL,
            target_user_pk INT NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_pk) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (target_user_pk) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE KEY uq_user_interest (user_pk, target_user_pk)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        # 2. 创建索引1
        """
        CREATE INDEX idx_user_interests_user_pk ON user_interests(user_pk)
        """,
        # 3. 创建索引2
        """
        CREATE INDEX idx_user_interests_target_user_pk ON user_interests(target_user_pk)
        """
    ]

    try:
        with engine.connect() as conn:
            for i, statement in enumerate(sql_statements, 1):
                statement = statement.strip()
                if not statement:
                    continue

                print(f"\nExecuting statement {i}/{len(sql_statements)}:")
                # 只显示前80个字符
                display_stmt = statement.replace('\n', ' ').replace('  ', ' ')
                print(f"  {display_stmt[:80]}..." if len(display_stmt) > 80 else f"  {display_stmt}")

                try:
                    conn.execute(text(statement))
                    conn.commit()
                    print("  [OK] Success")
                except Exception as e:
                    error_msg = str(e)
                    # 如果是索引已存在的错误，忽略
                    if "Duplicate key name" in error_msg or "already exists" in error_msg:
                        print(f"  [SKIP] Already exists")
                    else:
                        raise

        print("\n" + "=" * 60)
        print("[SUCCESS] Database migration completed!")
        print("=" * 60)
        print("\nTable structure:")
        print("  - user_interests")
        print("    - id (PRIMARY KEY)")
        print("    - user_pk (user who is interested)")
        print("    - target_user_pk (target user)")
        print("    - created_at (creation time)")
        print("    - updated_at (update time)")
        print("\nIndexes:")
        print("  - idx_user_interests_user_pk")
        print("  - idx_user_interests_target_user_pk")
        print("  - uq_user_interest (UNIQUE constraint)")
        print("\n" + "=" * 60)
        return True

    except Exception as e:
        print("\n" + "=" * 60)
        print(f"[ERROR] Migration failed: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
