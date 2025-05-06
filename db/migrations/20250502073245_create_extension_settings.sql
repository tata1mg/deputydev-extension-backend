-- migrate:up
CREATE TABLE IF NOT EXISTS extension_settings (
    id SERIAL PRIMARY KEY,
    user_team_id INT NOT NULL,
    client TEXT NOT NULL,
    settings JSON NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_extension_settings_user_team_id ON extension_settings(user_team_id);

-- migrate:down
DROP TABLE IF EXISTS extension_settings;
DROP INDEX IF EXISTS idx_extension_settings_user_team_id;
