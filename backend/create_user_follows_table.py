"""直接创建user_follows表的SQL脚本"""
CREATE_USER_FOLLOWS_TABLE = """
CREATE TABLE IF NOT EXISTS user_follows (
    id INT AUTO_INCREMENT PRIMARY KEY,
    follower_user_pk INT NOT NULL COMMENT '关注者用户ID',
    following_user_pk INT NOT NULL COMMENT '被关注的用户ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '关注时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uq_user_follow (follower_user_pk, following_user_pk),
    KEY ix_user_follows_follower_user_pk (follower_user_pk),
    KEY ix_user_follows_following_user_pk (following_user_pk),
    CONSTRAINT fk_user_follows_follower FOREIGN KEY (follower_user_pk) REFERENCES users (id) ON DELETE CASCADE,
    CONSTRAINT fk_user_follows_following FOREIGN KEY (following_user_pk) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

if __name__ == "__main__":
    import sys
    from sqlalchemy import create_engine, text
    from app.core.config import settings

    try:
        print("Connecting to database...")
        engine = create_engine(settings.DATABASE_URL)

        with engine.begin() as conn:
            print("Creating user_follows table...")
            conn.execute(text(CREATE_USER_FOLLOWS_TABLE))
            print("[OK] user_follows table created successfully!")

            # 更新alembic版本表
            print("Updating migration version...")
            conn.execute(text(
                "INSERT INTO alembic_version (version_num) VALUES ('20260609_01') "
                "ON DUPLICATE KEY UPDATE version_num='20260609_01'"
            ))
            print("[OK] Migration version updated!")

        print("\n[SUCCESS] Database migration completed!")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
