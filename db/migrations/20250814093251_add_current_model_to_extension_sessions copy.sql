-- migrate:up
ALTER TABLE extension_sessions
    ADD COLUMN current_model VARCHAR(255);

-- migrate:down
ALTER TABLE extension_sessions
    DROP COLUMN current_model;
