-- migrate:up
CREATE TABLE IF NOT EXISTS session_events (
    id SERIAL PRIMARY KEY,
    event_id UUID NOT NULL UNIQUE,
    session_id INT NOT NULL,
    event_type TEXT NOT NULL,
    lines INT NOT NULL,
    file_path TEXT,
    client_version TEXT NOT NULL,
    user_id INT NOT NULL,
    team_id INT NOT NULL,
    timestamp TIMESTAMP with time zone NOT NULL,
    created_at TIMESTAMP with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_session_events_session_id ON session_events(session_id);
CREATE INDEX idx_session_events_user_id ON session_events(user_id);
CREATE INDEX idx_session_events_team_id ON session_events(team_id);


-- migrate:down
DROP TABLE IF EXISTS session_events;

