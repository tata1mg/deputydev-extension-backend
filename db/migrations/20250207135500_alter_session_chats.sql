-- migrate:up
ALTER TABLE session_chats ADD COLUMN code_lines_count BIGINT;

-- migrate:down
ALTER TABLE session_chats DROP COLUMN code_lines_count;
