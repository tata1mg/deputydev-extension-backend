-- migrate:up

-- workspace_id, repo_id and pr_id are kept nullable because these can be created dynamically while reviewing PR in case of bitbucket
-- We would want to still save feedback if given before first PR reviewed for repo/workspace

CREATE TABLE IF NOT EXISTS feedbacks (
    id serial PRIMARY KEY,
    feedback_type varchar NOT NULL,
    feedback text NOT NULL,
    meta_info json NOT NULL,
    author_info json NOT NULL,
    organisation_id bigint NOT NULL,
    workspace_id bigint,
    repo_id bigint,
    pr_id bigint,
    scm_pr_id varchar not null,
    scm scm_type NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (pr_id) REFERENCES pull_requests(id),
    FOREIGN KEY (organisation_id) REFERENCES organisations(id),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
    FOREIGN KEY (repo_id) REFERENCES repos(id)
);

CREATE INDEX IF NOT EXISTS feedbacks_repo_id_created_idx ON feedbacks(repo_id, created_at, feedback_type);

-- migrate:down
DROP TABLE IF EXISTS feedbacks;