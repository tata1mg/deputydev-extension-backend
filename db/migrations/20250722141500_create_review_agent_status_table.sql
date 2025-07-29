-- migrate:up
CREATE TABLE IF NOT EXISTS review_agent_status (
    id BIGSERIAL PRIMARY KEY,
    review_id BIGINT NOT NULL,
    agent_id BIGINT NOT NULL,
    meta_info JSONB,
    llm_model TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (review_id) REFERENCES extension_reviews(id),
    FOREIGN KEY (agent_id) REFERENCES user_agents(id)
);

CREATE INDEX IF NOT EXISTS idx_review_agent_status_review_id ON review_agent_status(review_id);
CREATE INDEX IF NOT EXISTS idx_review_agent_status_agent_id ON review_agent_status(agent_id);
CREATE INDEX IF NOT EXISTS idx_review_agent_status_created_at ON review_agent_status(created_at);

-- migrate:down
DROP INDEX IF EXISTS idx_review_agent_status_created_at;
DROP INDEX IF EXISTS idx_review_agent_status_agent_id;
DROP INDEX IF EXISTS idx_review_agent_status_review_id;
DROP TABLE IF EXISTS review_agent_status;
