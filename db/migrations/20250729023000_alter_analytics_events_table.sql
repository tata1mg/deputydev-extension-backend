-- migrate:up
ALTER TABLE analytics_events
ALTER COLUMN session_id DROP NOT NULL;

-- migrate:down
ALTER TABLE analytics_events
ALTER COLUMN session_id SET NOT NULL;
