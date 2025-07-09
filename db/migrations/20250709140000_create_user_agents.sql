-- migrate:up
CREATE TABLE IF NOT EXISTS user_agents (
    id BIGSERIAL PRIMARY KEY,
    agent_name CITEXT NOT NULL,
    display_name VARCHAR(1000),
    custom_prompt TEXT DEFAULT '',
    exclusions JSONB DEFAULT '[]',
    inclusions JSONB DEFAULT '[]',
    confidence_score FLOAT DEFAULT 0.9,
    objective TEXT DEFAULT 'Responsibility of this agent is checking security issues',
    is_custom_agent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- migrate:down
DROP TABLE IF EXISTS user_agents;