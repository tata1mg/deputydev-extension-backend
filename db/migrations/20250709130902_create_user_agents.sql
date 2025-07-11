-- migrate:up
CREATE TABLE IF NOT EXISTS user_agents (
    id BIGSERIAL PRIMARY KEY,
    agent_name text NOT NULL,
    display_name VARCHAR(1000) NOT NULL ,
    custom_prompt TEXT DEFAULT '',
    exclusions JSONB NOT NULL DEFAULT '[]',
    inclusions JSONB NOT NULL DEFAULT '[]',
    confidence_score DOUBLE PRECISION NOT NULL DEFAULT 0.9,
    objective TEXT,
    is_custom_agent BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- migrate:down

