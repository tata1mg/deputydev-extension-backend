-- migrate:up
CREATE TABLE IF NOT EXISTS extension_sessions (
    id SERIAL PRIMARY KEY,
    session_id INT NOT NULL,
    user_team_id INT NOT NULL,
    summary TEXT,
    pinned_rank INT DEFAULT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    session_type TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP DEFAULT NULL,
    FOREIGN KEY (session_id) REFERENCES message_sessions(id)
);

-- migrate:down
DROP TABLE IF EXISTS extension_sessions;

