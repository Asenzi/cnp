-- 创建用户关注表
-- 请在MySQL数据库中直接执行此脚本

CREATE TABLE IF NOT EXISTS user_follows (
    id INT AUTO_INCREMENT PRIMARY KEY,
    follower_user_pk INT NOT NULL COMMENT '关注者用户ID',
    following_user_pk INT NOT NULL COMMENT '被关注的用户ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '关注时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 唯一约束：同一用户不能重复关注
    UNIQUE KEY uq_user_follow (follower_user_pk, following_user_pk),

    -- 索引
    KEY ix_user_follows_follower_user_pk (follower_user_pk),
    KEY ix_user_follows_following_user_pk (following_user_pk),

    -- 外键约束
    CONSTRAINT fk_user_follows_follower
        FOREIGN KEY (follower_user_pk)
        REFERENCES users (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_user_follows_following
        FOREIGN KEY (following_user_pk)
        REFERENCES users (id)
        ON DELETE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='用户关注关系表';

-- 更新Alembic版本记录（如果使用Alembic管理迁移）
INSERT INTO alembic_version (version_num) VALUES ('20260609_01')
ON DUPLICATE KEY UPDATE version_num='20260609_01';

-- 验证表创建成功
SELECT 'user_follows表创建成功！' AS status;
SELECT COUNT(*) AS total_follows FROM user_follows;
