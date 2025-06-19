-- migrate:up
ALTER TABLE error_analytics_events
ADD COLUMN stack_trace TEXT,
ADD COLUMN user_system_info JSONB;



-- migrate:down
ALTER TABLE error_analytics_events
DROP COLUMN IF EXISTS stack_trace,
DROP COLUMN IF EXISTS user_system_info;

