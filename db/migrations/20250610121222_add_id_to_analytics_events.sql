-- migrate:up
ALTER TABLE error_analytics_events
ADD COLUMN error_id UUID,
ADD CONSTRAINT error_analytics_events_error_id_key UNIQUE (error_id);

ALTER TABLE analytics_events
ADD COLUMN event_id UUID,
ADD CONSTRAINT analytics_events_event_id_key UNIQUE (event_id);

-- migrate:down
ALTER TABLE error_analytics_events
DROP CONSTRAINT IF EXISTS error_analytics_events_error_id_key,
DROP COLUMN IF EXISTS error_id;

ALTER TABLE analytics_events
DROP CONSTRAINT IF EXISTS analytics_events_event_id_key,
DROP COLUMN IF EXISTS event_id;