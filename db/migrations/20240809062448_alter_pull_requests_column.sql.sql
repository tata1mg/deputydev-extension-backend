-- migrate:up
ALTER TABLE pull_requests ADD loc_changed bigint;

-- migrate:down
ALTER TABLE pull_requests DROP COLUMN loc_changed;