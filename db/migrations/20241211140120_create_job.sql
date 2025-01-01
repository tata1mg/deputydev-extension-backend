-- migrate:up
CREATE TABLE IF NOT EXISTS job (
    id SERIAL PRIMARY KEY,
    type VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    session_id VARCHAR NOT NULL,
    final_output JSON,
    meta_info JSON,
    team_id INT NOT NULL,
    advocacy_id INT NOT NULL,
    user_email VARCHAR,
    user_name VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- migrate:down
DROP TABLE IF EXISTS job;

