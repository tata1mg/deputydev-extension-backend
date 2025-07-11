-- migrate:up
CREATE TABLE IF NOT EXISTS user_agent_comment_mapping (
    id BIGSERIAL PRIMARY KEY,
    agent_id BIGINT NOT NULL REFERENCES user_agents(id),
    comment_id BIGINT NOT NULL REFERENCES ide_reviews_comments(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE (agent_id, comment_id)
);

-- migrate:down
DROP TABLE IF EXISTS user_agent_comment_mapping;