-- migrate:up
CREATE TABLE chats
(
    id           SERIAL PRIMARY KEY,
    session_id   INT                                                NOT NULL,
    actor        VARCHAR(16)                                        NOT NULL,
    message_type VARCHAR(16)                                        NOT NULL,
    message_data JSONB                                              NOT NULL,
    metadata     JSONB                                              NOT NULL,
    created_at   timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at   timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Add indexes as specified in the model
CREATE INDEX chats_session_id ON chats (session_id);
CREATE INDEX chats_actor ON chats (actor);
CREATE INDEX chats_message_type ON chats (message_type);

-- migrate:down
DROP TABLE chats;