-- migrate:up
CREATE TABLE IF NOT EXISTS query_summaries (
    id SERIAL PRIMARY KEY,
    summary TEXT NOT NULL,
    query_id INT NOT NULL,
    session_id INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- migrate:down
DROP TABLE IF EXISTS query_summaries;