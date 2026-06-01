-- MySQL 版本：创建用户感兴趣关系表
CREATE TABLE IF NOT EXISTS user_interests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_pk INT NOT NULL,
    target_user_pk INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_pk) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (target_user_pk) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uq_user_interest (user_pk, target_user_pk)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建索引以提高查询性能
CREATE INDEX idx_user_interests_user_pk ON user_interests(user_pk);
CREATE INDEX idx_user_interests_target_user_pk ON user_interests(target_user_pk);

