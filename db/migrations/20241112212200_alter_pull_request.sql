-- migrate:up

ALTER TABLE pull_requests
    ADD COLUMN destination_commit_id varchar NOT NULL DEFAULT 'destination_commit';

ALTER TABLE pull_requests
    ADD COLUMN iteration bigint default 1;

ALTER TABLE pull_requests
    DROP CONSTRAINT IF EXISTS pull_requests_repo_id_scm_pr_id_key,
    ADD CONSTRAINT pull_requests_unique_key UNIQUE (scm_pr_id, repo_id, commit_id, destination_commit_id);




-- migrate:down
ALTER TABLE pull_requests
    DROP CONSTRAINT IF EXISTS pull_requests_unique_key,
    ADD CONSTRAINT pull_requests_repo_id_scm_pr_id_key UNIQUE (repo_id, scm_pr_id);

ALTER TABLE pull_requests
    DROP COLUMN IF EXISTS iteration;

ALTER TABLE pull_requests
    DROP COLUMN IF EXISTS destination_commit_id;
