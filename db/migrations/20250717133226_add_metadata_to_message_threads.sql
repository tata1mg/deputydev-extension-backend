-- migrate:up
ALTER TABLE message_threads ADD COLUMN IF NOT EXISTS metadata JSON;

-- migrate:down
ALTER TABLE message_threads DROP COLUMN IF EXISTS metadata;