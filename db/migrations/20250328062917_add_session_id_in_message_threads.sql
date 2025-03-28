-- migrate:up
ALTER TABLE pull_requests ADD COLUMN IF NOT EXISTS session_id INT;


-- migrate:down
ALTER TABLE pull_requests DROP COLUMN IF EXISTS session_id;

