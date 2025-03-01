-- migrate:up
CREATE TABLE IF NOT EXISTS message_sessions (
    id SERIAL PRIMARY KEY,
    client TEXT NOT NULL,
    client_version TEXT,
    summary TEXT,
    user_team_id INT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP DEFAULT NULL,
);

-- migrate:down
DROP TABLE IF EXISTS message_sessions;