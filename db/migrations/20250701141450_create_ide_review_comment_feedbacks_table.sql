-- migrate:up
CREATE TABLE IF NOT EXISTS ide_review_comment_feedbacks (
    id BIGSERIAL PRIMARY KEY,
    comment_id BIGINT NOT NULL,
    feedback_comment TEXT,
    "like" BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (comment_id) REFERENCES ide_reviews_comments(id)
);

CREATE INDEX IF NOT EXISTS idx_ide_review_comment_feedbacks_comment_id ON ide_review_comment_feedbacks(comment_id);
CREATE INDEX IF NOT EXISTS idx_ide_review_comment_feedbacks_created_at ON ide_review_comment_feedbacks(created_at);

-- migrate:down
DROP INDEX IF EXISTS idx_ide_review_comment_feedbacks_created_at;
DROP INDEX IF EXISTS idx_ide_review_comment_feedbacks_comment_id;
DROP TABLE IF EXISTS ide_review_comment_feedbacks;