-- migrate:up
CREATE TABLE IF NOT EXISTS chat_attachments (
    id SERIAL PRIMARY KEY,
    file_type VARCHAR NOT NULL,
    file_name VARCHAR NOT NULL,
    s3_key VARCHAR NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- migrate:down
DROP TABLE IF EXISTS chat_attachments;
