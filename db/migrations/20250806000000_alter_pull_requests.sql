-- migrate:up
ALTER TABLE pull_requests
    DROP CONSTRAINT IF EXISTS pull_requests_unique_key;

-- migrate:down
ALTER TABLE pull_requests
    ADD CONSTRAINT pull_requests_unique_key UNIQUE (scm_pr_id, repo_id, commit_id, destination_commit_id);
