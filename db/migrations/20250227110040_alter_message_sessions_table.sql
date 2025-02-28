-- migrate:up
ALTER TABLE message_sessions ADD COLUMN status TEXT NOT NULL DEFAULT 'ACTIVE';
ALTER TABLE message_sessions ADD COLUMN deleted_at TIMESTAMP;

-- migrate:down
ALTER TABLE message_sessions DROP COLUMN status;
ALTER TABLE message_sessions DROP COLUMN deleted_at;
