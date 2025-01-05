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

CREATE INDEX idx_session_chats_session_id ON session_chats(session_id);
CREATE INDEX idx_session_chats_prompt_type ON session_chats(prompt_type);


-- migrate:down
DROP INDEX IF EXISTS idx_session_chats_session_id;
DROP INDEX IF EXISTS idx_session_chats_prompt_type;
DROP TABLE IF EXISTS session_chats;
