-- migrate:up
CREATE TABLE IF NOT EXISTS ide_reviews_comments (
    id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL,
    comment TEXT NOT NULL,
    agent_id INTEGER NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    file_path TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    line_number INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (review_id) REFERENCES extension_reviews(id)
);

CREATE INDEX IF NOT EXISTS idx_ide_reviews_comments_review_id ON ide_reviews_comments(review_id);
CREATE INDEX IF NOT EXISTS idx_ide_reviews_comments_agent_id ON ide_reviews_comments(agent_id);
CREATE INDEX IF NOT EXISTS idx_ide_reviews_comments_file_path ON ide_reviews_comments(file_path);
CREATE INDEX IF NOT EXISTS idx_ide_reviews_comments_created_at ON ide_reviews_comments(created_at);

-- migrate:down
DROP INDEX IF EXISTS idx_ide_reviews_comments_created_at;
DROP INDEX IF EXISTS idx_ide_reviews_comments_file_path;
DROP INDEX IF EXISTS idx_ide_reviews_comments_agent_id;
DROP INDEX IF EXISTS idx_ide_reviews_comments_review_id;
DROP TABLE IF EXISTS ide_reviews_comments;