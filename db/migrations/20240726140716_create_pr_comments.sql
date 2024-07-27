-- migrate:up
CREATE TABLE IF NOT EXISTS pr_comments (
    id serial PRIMARY KEY,
    iteration smallint NOT NULL,
    llm_confidence_score double precision NOT NULL,
    llm_source_model varchar NOT NULL,
    organisation_id bigint NOT NULL,
    scm scm_type NOT NULL,
    workspace_id bigint NOT NULL,
    repo_id bigint NOT NULL,
    pr_id bigint NOT NULL,
    scm_comment_id varchar NOT NULL,
    scm_author_id varchar NOT NULL,
    author_name varchar NOT NULL,
    bucket_id integer NOT NULL,
    meta_info json,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE (pr_id, scm_comment_id),
    FOREIGN KEY (bucket_id) REFERENCES buckets(id),
    FOREIGN KEY (organisation_id) REFERENCES organisations(id),
    FOREIGN KEY (pr_id) REFERENCES pull_requests(id),
    FOREIGN KEY (repo_id) REFERENCES repos(id),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
);

CREATE INDEX IF NOT EXISTS pr_comments_organisation_id_created_scm_idx ON pr_comments(organisation_id, created_at, scm);
CREATE INDEX IF NOT EXISTS pr_comments_pr_id_created_idx ON pr_comments(pr_id, created_at);
CREATE INDEX IF NOT EXISTS pr_comments_repo_id_created_idx ON pr_comments(repo_id, created_at);
CREATE INDEX IF NOT EXISTS pr_comments_workspace_id_created_idx ON pr_comments(workspace_id, created_at);

-- migrate:down
DROP TABLE IF EXISTS pr_comments;
