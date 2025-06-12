-- migrate:up
ALTER TABLE chat_attachments 
ADD COLUMN IF NOT EXISTS status VARCHAR DEFAULT NULL;

-- migrate:down
ALTER TABLE chat_attachments DROP COLUMN IF EXISTS status;
