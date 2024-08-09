-- migrate:up
ALTER TABLE pull_requests ADD scm_approval_time timestamp with time zone;

-- migrate:down
ALTER TABLE pull_requests DROP COLUMN scm_approval_time;