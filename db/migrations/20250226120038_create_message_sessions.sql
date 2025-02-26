-- migrate:up
CREATE TABLE IF NOT EXISTS message_sessions (
    id SERIAL PRIMARY KEY,
    client TEXT NOT NULL,
    client_version TEXT,
    summary TEXT,
    user_team_id INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- migrate:down
DROP TABLE IF EXISTS message_sessions;