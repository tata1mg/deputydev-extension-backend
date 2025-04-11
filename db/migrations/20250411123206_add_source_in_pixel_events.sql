-- migrate:up
ALTER TABLE pixel_events ADD COLUMN IF NOT EXISTS source TEXT;


-- migrate:down
ALTER TABLE pixel_events DROP COLUMN IF EXISTS source;

