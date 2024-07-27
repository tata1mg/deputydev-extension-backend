-- migrate:up
CREATE TABLE IF NOT EXISTS organisations (
    id serial PRIMARY KEY,
    name citext UNIQUE NOT NULL,
    status varchar NOT NULL,
    email varchar NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- migrate:down
DROP TABLE IF EXISTS organisations;
