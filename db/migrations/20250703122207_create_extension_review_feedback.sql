-- migrate:up
CREATE TABLE IF NOT EXISTS extension_reviews_feedbacks (
    id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL,
    feedback_comment TEXT,
    "like" BOOLEAN,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (review_id) REFERENCES extension_reviews(id)
);

CREATE INDEX IF NOT EXISTS idx_ide_review_feedbacks_review_id ON extension_reviews_feedbacks(review_id);

-- migrate:down

