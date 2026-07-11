#!/usr/bin/env python3
"""清除用户实名认证状态"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 创建数据库连接
DATABASE_URL = f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}?charset=utf8mb4"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def clear_user_verification(search_term: str):
    """清除用户的实名认证状态"""
    db = SessionLocal()
    try:
        # 查找用户
        query = text("""
            SELECT id, user_id, nickname, phone, wechat_openid, is_verified
            FROM users
            WHERE nickname LIKE :search OR wechat_openid LIKE :search
            LIMIT 5
        """)
        result = db.execute(query, {"search": f"%{search_term}%"})
        users = result.fetchall()

        if not users:
            print(f"未找到匹配 '{search_term}' 的用户")
            return

        print(f"\n找到 {len(users)} 个用户:")
        for user in users:
            print(f"  - {user.nickname} (user_id: {user.user_id}, is_verified: {user.is_verified})")

        if len(users) == 1:
            user = users[0]
            user_id = user.id

            # 清除 users 表的 is_verified 字段
            update_user = text("UPDATE users SET is_verified = 0 WHERE id = :user_id")
            db.execute(update_user, {"user_id": user_id})

            # 删除实名认证相关记录
            # 1. 删除实名认证会话记录 (注意字段名是 user_pk)
            delete_sessions = text("DELETE FROM user_real_name_verification_sessions WHERE user_pk = :user_id")
            db.execute(delete_sessions, {"user_id": user_id})

            # 2. 删除实名认证资料 (注意字段名是 user_pk)
            delete_profile = text("DELETE FROM user_real_name_profiles WHERE user_pk = :user_id")
            db.execute(delete_profile, {"user_id": user_id})

            db.commit()

            print(f"\n[OK] 已清除用户 {user.nickname} 的实名认证状态")
            print("  - users.is_verified 设置为 False")
            print("  - 删除了 user_real_name_verification_sessions 记录")
            print("  - 删除了 user_real_name_profiles 记录")
        else:
            print("\n找到多个用户，请提供更精确的搜索条件")

    except Exception as e:
        db.rollback()
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    search_term = "T8Ns"
    if len(sys.argv) > 1:
        search_term = sys.argv[1]

    clear_user_verification(search_term)
