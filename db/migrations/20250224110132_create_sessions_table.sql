-- migrate:up
CREATE TABLE IF NOT EXISTS message_sessions (
    id SERIAL PRIMARY KEY,
    summary TEXT NOT NULL,
    user_team_id INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_team_id) REFERENCES user_teams(id)
);

CREATE INDEX idx_message_sessions_user_team_id ON message_sessions(user_team_id);

-- migrate:down
DROP TABLE IF EXISTS message_sessions;
