-- migrate:up
CREATE TABLE IF NOT EXISTS error_analytics_events (
    id              SERIAL PRIMARY KEY,
    user_email      TEXT,
    error_type      TEXT NOT NULL,
    error_data      JSONB NOT NULL,
    repo_name       TEXT,
    error_source    TEXT NOT NULL,
    client_version  TEXT NOT NULL,
    timestamp       TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_team_id    BIGINT,
    session_id      BIGINT,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Single-column indexes for filtering
CREATE INDEX IF NOT EXISTS idx_error_analytics_user_email_not_null
    ON error_analytics_events(user_email)
    WHERE user_email IS NOT NULL;


CREATE INDEX IF NOT EXISTS idx_error_analytics_timestamp
    ON error_analytics_events(timestamp DESC);

-- Composite index for dashboard queries (email + timestamp)

CREATE INDEX idx_error_analytics_useremail_time_not_null
    ON error_analytics_events(user_email, timestamp DESC)
    WHERE user_email IS NOT NULL;

-- migrate:down
DROP TABLE IF EXISTS error_analytics_events;
