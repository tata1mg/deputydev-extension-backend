-- migrate:up
CREATE TABLE IF NOT EXISTS ide_reviews_comments (
    id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL,
    comment TEXT NOT NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    file_path TEXT NOT NULL,
    line_hash TEXT NOT NULL,
    line_number INTEGER NOT NULL,
    tag text NOT NULL,
    is_valid BOOLEAN NOT NULL,
    corrective_code TEXT,
    rationale TEXT,
    confidence_score NUMERIC(5, 4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (review_id) REFERENCES extension_reviews(id)
);

CREATE INDEX IF NOT EXISTS idx_ide_reviews_comments_review_id ON ide_reviews_comments(review_id);
CREATE INDEX IF NOT EXISTS idx_ide_reviews_comments_file_path ON ide_reviews_comments(file_path);
CREATE INDEX IF NOT EXISTS idx_ide_reviews_comments_created_at ON ide_reviews_comments(created_at);

-- migrate:down
DROP INDEX IF EXISTS idx_ide_reviews_comments_created_at;
DROP INDEX IF EXISTS idx_ide_reviews_comments_file_path;
DROP INDEX IF EXISTS idx_ide_reviews_comments_review_id;
DROP TABLE IF EXISTS ide_reviews_comments;