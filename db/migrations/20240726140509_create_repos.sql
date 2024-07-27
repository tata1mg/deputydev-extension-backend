-- migrate:up
CREATE TABLE IF NOT EXISTS repos (
    id serial PRIMARY KEY,
    name citext NOT NULL,
    organisation_id bigint NOT NULL,
    scm scm_type NOT NULL,
    workspace_id bigint NOT NULL,
    scm_repo_id varchar NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE (workspace_id, scm_repo_id),
    FOREIGN KEY (organisation_id) REFERENCES organisations(id),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
);

CREATE INDEX IF NOT EXISTS repos_workspace_id_idx ON repos(workspace_id);

-- migrate:down
DROP TABLE IF EXISTS repos;
