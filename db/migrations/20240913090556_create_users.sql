-- migrate:up
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email citext UNIQUE NOT NULL,
    name VARCHAR NOT NULL,
    org_name VARCHAR,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- migrate:down
DROP TABLE IF EXISTS users;
