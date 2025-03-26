-- migrate:up
CREATE TABLE IF NOT EXISTS pixel_events (
    id SERIAL PRIMARY KEY,
    event_id UUID NOT NULL UNIQUE,
    session_id INT NOT NULL,
    event_type TEXT NOT NULL,
    lines INT NOT NULL,
    file_path TEXT,
    client_version TEXT NOT NULL,
    client TEXT NOT NULL,
    user_id INT NOT NULL,
    team_id INT NOT NULL,
    timestamp TIMESTAMP with time zone NOT NULL,
    created_at TIMESTAMP with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pixel_events_session_id ON pixel_events(session_id);
CREATE INDEX idx_pixel_events_user_id ON pixel_events(user_id);
CREATE INDEX idx_pixel_events_team_id ON pixel_events(team_id);
CREATE INDEX idx_pixel_events_user_team ON pixel_events(user_id, team_id);


-- migrate:down
DROP INDEX IF EXISTS idx_pixel_events_session_id;
DROP INDEX IF EXISTS idx_pixel_events_user_id;
DROP INDEX IF EXISTS idx_pixel_events_team_id;
DROP INDEX IF EXISTS idx_pixel_events_user_team;
DROP TABLE IF EXISTS pixel_events;

