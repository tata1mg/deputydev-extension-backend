-- migrate:up
CREATE TABLE IF NOT EXISTS experiments (
    id serial PRIMARY KEY,
    review_status varchar NOT NULL,
    scm_pr_id varchar NOT NULL,
    organisation_id bigint NOT NULL,
    workspace_id bigint NOT NULL,
    repo_id bigint NOT NULL,
    cohort varchar NOT NULL,
    scm scm_type NOT NULL,
    pr_id bigint NOT NULL,
    merge_time_in_sec bigint,
    human_comment_count bigint,
    llm_comment_count bigint,
    scm_creation_time timestamp with time zone NOT NULL,
    scm_merge_time timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (organisation_id) REFERENCES organisations(id),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
    FOREIGN KEY (repo_id) REFERENCES repos(id),
    FOREIGN KEY (pr_id) REFERENCES pull_requests(id)
);

CREATE INDEX IF NOT EXISTS pr_experiments_org_id_repo_id_scm_cohort_idx ON experiments(repo_id, created_at, cohort);

-- migrate:down
DROP TABLE IF EXISTS experiments;