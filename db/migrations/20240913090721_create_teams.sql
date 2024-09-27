-- migrate:up
CREATE TABLE teams (
    id BIGSERIAL PRIMARY KEY,
    name citext UNIQUE NOT NULL,
    llm_model VARCHAR,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- migrate:down
DROP TABLE IF EXISTS teams;
