-- migrate:up
CREATE TABLE IF NOT EXISTS buckets (
    id serial PRIMARY KEY,
    name citext UNIQUE NOT NULL,
    weight smallint,
    bucket_type varchar NOT NULL,
    status varchar NOT NULL,
    is_llm_suggested boolean NOT NULL,
    description text DEFAULT ''::text NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- migrate:down
DROP TABLE IF EXISTS buckets;
