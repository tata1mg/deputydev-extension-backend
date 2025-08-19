-- migrate:up
CREATE TABLE IF NOT EXISTS review_agent_chats (
    id SERIAL PRIMARY KEY,
    session_id INT NOT NULL,
    agent_id VARCHAR(64) NOT NULL,
    actor VARCHAR(16) NOT NULL,
    message_type VARCHAR(16) NOT NULL,
    message_data JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Add indexes as specified in the model
CREATE INDEX IF NOT EXISTS idx_review_agent_chats_session_id ON review_agent_chats(session_id);
CREATE INDEX IF NOT EXISTS idx_review_agent_chats_actor ON review_agent_chats(actor);
CREATE INDEX IF NOT EXISTS idx_review_agent_chats_message_type ON review_agent_chats(message_type);

-- migrate:down
DROP INDEX IF EXISTS idx_review_agent_chats_message_type;
DROP INDEX IF EXISTS idx_review_agent_chats_actor;
DROP INDEX IF EXISTS idx_review_agent_chats_session_id;
DROP TABLE IF EXISTS review_agent_chats;