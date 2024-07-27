-- migrate:up
CREATE TABLE IF NOT EXISTS org_scm_accounts (
    id serial PRIMARY KEY,
    organisation_id bigint NOT NULL,
    scm scm_type NOT NULL,
    token varchar,
    scm_account_id varchar,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE (organisation_id, scm),
    FOREIGN KEY (organisation_id) REFERENCES organisations(id)
);

-- migrate:down
DROP TABLE IF EXISTS org_scm_accounts;
