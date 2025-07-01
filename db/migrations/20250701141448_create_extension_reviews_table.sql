-- migrate:up
CREATE TABLE IF NOT EXISTS extension_reviews (
    id BIGSERIAL PRIMARY KEY,
    repo_id BIGINT NOT NULL,
    loc INTEGER NOT NULL,
    reviewed_files JSONB NOT NULL,
    execution_time_seconds INTEGER,
    status VARCHAR(20) NOT NULL,
    source_branch TEXT,
    target_branch TEXT,
    source_commit TEXT,
    target_commit TEXT,
    fail_message TEXT,
    review_datetime TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    deletion_datetime TIMESTAMP,
    meta_info JSONB,
    diff_s3_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (repo_id) REFERENCES repos(id)
);

CREATE INDEX IF NOT EXISTS idx_extension_reviews_user_repo_id ON extension_reviews(repo_id);
CREATE INDEX IF NOT EXISTS idx_extension_reviews_created_at ON extension_reviews(created_at);
CREATE INDEX IF NOT EXISTS idx_extension_reviews_status ON extension_reviews(status);

-- migrate:down
DROP INDEX IF EXISTS idx_extension_reviews_status;
DROP INDEX IF EXISTS idx_extension_reviews_created_at;
DROP INDEX IF EXISTS idx_extension_reviews_user_repo_id;
DROP TABLE IF EXISTS extension_reviews;