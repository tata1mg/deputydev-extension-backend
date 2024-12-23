-- migrate:up
CREATE TABLE agents
(
    id           SERIAL PRIMARY KEY,
    agent_id     UUID                                               NOT NULL,
    agent_name   TEXT                                               NOT NULL,
    display_name TEXT                                               NOT NULL,
    repo_id      INT                                                NOT NULL REFERENCES repos (id),
    created_at   timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at   timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE (agent_id, repo_id)
);

-- Add separate index on agent_id
CREATE INDEX idx_agent_id ON agents (agent_id);

-- Add separate index on repo_id
CREATE INDEX idx_repo_id ON agents (repo_id);

-- migrate:down
drop table agents;

