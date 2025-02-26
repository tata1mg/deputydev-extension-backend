-- migrate:up
CREATE TABLE IF NOT EXISTS message_threads (
    id SERIAL PRIMARY KEY,
    session_id INT NOT NULL,
    actor TEXT NOT NULL,
    query_id INT,
    message_type TEXT NOT NULL,
    conversation_chain JSON,
    message_data JSON NOT NULL,
    data_hash TEXT NOT NULL,
    usage JSON,
    llm_model TEXT NOT NULL,
    prompt_type TEXT NOT NULL,
    query_vars JSON,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- migrate:down
DROP TABLE IF EXISTS message_threads;