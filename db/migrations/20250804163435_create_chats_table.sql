-- migrate:up
CREATE TABLE agent_chats
(
    id           SERIAL PRIMARY KEY,
    session_id   INT                                                NOT NULL,
    query_id     VARCHAR                                            NOT NULL,
    actor        VARCHAR(16)                                        NOT NULL,
    message_type VARCHAR(16)                                        NOT NULL,
    message_data JSONB                                              NOT NULL,
    metadata     JSONB                                              NOT NULL,
    previous_queries JSONB                                          NOT NULL,
    created_at   timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at   timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Add indexes as specified in the model
CREATE INDEX agent_chats_session_id ON agent_chats (session_id);
CREATE INDEX agent_chats_actor ON agent_chats (actor);
CREATE INDEX agent_chats_message_type ON agent_chats (message_type);

-- migrate:down
DROP TABLE agent_chats;