-- migrate:up
DROP INDEX IF EXISTS prs_repo_id_created_idx;

CREATE INDEX pull_requests_repo_id_created_at_itr_idx
ON pull_requests(repo_id, created_at, iteration);

-- migrate:down
DROP INDEX IF EXISTS pull_requests_repo_id_created_at_itr_idx;
CREATE INDEX IF NOT EXISTS prs_repo_id_created_idx ON pull_requests(repo_id, created_at);