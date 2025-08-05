-- migrate:up
ALTER TABLE message_threads ADD COLUMN IF NOT EXISTS cost DOUBLE PRECISION;

-- migrate:down
ALTER TABLE message_threads DROP COLUMN IF EXISTS cost;
