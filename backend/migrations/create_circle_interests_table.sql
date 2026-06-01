CREATE TABLE IF NOT EXISTS circle_interests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_pk INT NOT NULL,
    circle_pk INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_pk) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (circle_pk) REFERENCES circles(id) ON DELETE CASCADE,
    UNIQUE KEY uq_circle_interest (user_pk, circle_pk)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_circle_interests_user_pk ON circle_interests(user_pk);
CREATE INDEX idx_circle_interests_circle_pk ON circle_interests(circle_pk);
