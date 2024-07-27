-- migrate:up
CREATE TABLE IF NOT EXISTS pull_requests (
    id serial PRIMARY KEY,
    review_status varchar NOT NULL,
    quality_score integer,
    title text,
    organisation_id bigint NOT NULL,
    scm scm_type NOT NULL,
    workspace_id bigint NOT NULL,
    repo_id bigint NOT NULL,
    scm_pr_id varchar NOT NULL,
    scm_author_id varchar NOT NULL,
    author_name varchar NOT NULL,
    meta_info json,
    source_branch varchar NOT NULL,
    destination_branch varchar NOT NULL,
    scm_creation_time timestamp with time zone,
    scm_merge_time timestamp with time zone,
    commit_id varchar NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE (repo_id, scm_pr_id),
    FOREIGN KEY (organisation_id) REFERENCES organisations(id),
    FOREIGN KEY (repo_id) REFERENCES repos(id),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
);


CREATE INDEX IF NOT EXISTS prs_organisation_id_created_scm_idx ON pull_requests(organisation_id, created_at, scm);
CREATE INDEX IF NOT EXISTS prs_repo_id_created_idx ON pull_requests(repo_id, created_at);
CREATE INDEX IF NOT EXISTS prs_workspace_id_created_idx ON pull_requests(workspace_id, created_at);

-- migrate:down
DROP TABLE IF EXISTS pull_requests;
