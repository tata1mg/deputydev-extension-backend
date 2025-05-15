-- migrate:up
ALTER TABLE pull_requests
ADD COLUMN IF NOT EXISTS session_ids jsonb;

UPDATE pull_requests
SET session_ids = CASE
    WHEN session_id IS NOT NULL THEN jsonb_build_array(session_id)
    ELSE '[]'::jsonb
END;

-- migrate:down
ALTER TABLE pull_requests
DROP COLUMN IF EXISTS session_ids;
