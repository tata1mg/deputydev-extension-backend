-- migrate:up
CREATE TABLE IF NOT EXISTS workspaces (
    id serial PRIMARY KEY,
    scm_workspace_id varchar NOT NULL,
    name citext NOT NULL,
    organisation_id bigint NOT NULL,
    scm scm_type NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE (scm, scm_workspace_id),
    FOREIGN KEY (organisation_id) REFERENCES organisations(id)
);

-- migrate:down
DROP TABLE IF EXISTS workspaces;
