-- migrate:up
ALTER TABLE message_threads
    ADD COLUMN migrated BOOLEAN DEFAULT FALSE;

-- migrate:down
ALTER TABLE message_threads
    DROP COLUMN migrated;
