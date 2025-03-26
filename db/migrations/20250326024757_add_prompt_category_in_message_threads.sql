-- migrate:up
ALTER TABLE message_threads ADD COLUMN IF NOT EXISTS prompt_category VARCHAR NOT NULL DEFAULT 'UNSET';


-- migrate:down
ALTER TABLE message_threads DROP COLUMN IF EXISTS prompt_category;

