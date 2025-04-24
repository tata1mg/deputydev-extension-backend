-- migrate:up
CREATE TABLE IF NOT EXISTS urls
(
    id           SERIAL PRIMARY KEY,
    name         TEXT    NOT NULL,
    url          TEXT    NOT NULL,
    user_team_id INTEGER NOT NULL,
    is_deleted   BOOLEAN   DEFAULT FALSE,
    last_indexed TIMESTAMP,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (url, user_team_id)
);


-- migrate:down
DROP TABLE IF EXISTS urls;
