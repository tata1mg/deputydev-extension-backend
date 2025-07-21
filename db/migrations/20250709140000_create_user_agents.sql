-- migrate:up
CREATE TABLE IF NOT EXISTS user_agents (
    id BIGSERIAL PRIMARY KEY,
    user_team_id INT NOT NULL,
    agent_name CITEXT NOT NULL,
    display_name VARCHAR(1000) NOT NULL,
    custom_prompt TEXT DEFAULT '',
    exclusions JSONB DEFAULT '[]',
    inclusions JSONB DEFAULT '[]',
    confidence_score FLOAT DEFAULT 0.9,
    objective TEXT DEFAULT '',
    is_custom_agent BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS user_agents_user_team_id_agent_name_unique_active
ON user_agents (user_team_id, agent_name)
WHERE is_deleted = FALSE;

-- migrate:down
DROP TABLE IF EXISTS user_agents;