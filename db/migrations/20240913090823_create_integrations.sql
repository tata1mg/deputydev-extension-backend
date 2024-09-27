-- migrate:up
CREATE TABLE integrations (
    id BIGSERIAL PRIMARY KEY,
    team_id BIGINT NOT NULL,
    client VARCHAR NOT NULL,
    client_account_id VARCHAR,
    client_username VARCHAR,
    is_connected BOOLEAN NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (team_id) REFERENCES teams(id),
    UNIQUE (team_id, client)
);


-- migrate:down
DROP TABLE IF EXISTS integrations;