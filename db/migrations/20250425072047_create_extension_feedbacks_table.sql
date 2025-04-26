-- migrate:up
CREATE TABLE IF NOT EXISTS extension_feedbacks (
    id SERIAL PRIMARY KEY,
    query_id INT NOT NULL,
    feedback VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_extension_feedbacks_query_id ON extension_feedbacks(query_id);


-- migrate:down
DROP INDEX IF EXISTS idx_extension_feedbacks_query_id;
DROP TABLE IF EXISTS extension_feedbacks;