-- migrate:up
DROP INDEX IF EXISTS prs_repo_id_created_idx;

CREATE INDEX pull_requests_repo_id_created_at_itr_idx
ON pull_requests(repo_id, created_at, iteration);

CREATE UNIQUE INDEX comment_bucket_mapping_bucket_id_pr_comment_id_unique
ON comment_bucket_mapping(bucket_id, pr_comment_id);

-- migrate:down
DROP INDEX IF EXISTS comment_bucket_mapping_bucket_id_pr_comment_id_unique;
DROP INDEX IF EXISTS pull_requests_repo_id_created_at_itr_idx;
CREATE INDEX IF NOT EXISTS prs_repo_id_created_idx ON pull_requests(repo_id, created_at);