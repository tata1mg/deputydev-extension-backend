-- migrate:up
CREATE TABLE IF NOT EXISTS session_chats (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR NOT NULL,
    prompt_type VARCHAR NOT NULL,
    llm_prompt VARCHAR NOT NULL,
    llm_response VARCHAR NOT NULL,
    llm_model VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- migrate:down
DROP TABLE IF EXISTS session_chats;
