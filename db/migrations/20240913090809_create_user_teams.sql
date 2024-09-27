-- migrate:up
CREATE TABLE user_teams (
    id BIGSERIAL PRIMARY KEY,
    user_id bigint NOT NULL,
    team_id BIGINT NOT NULL,
    role VARCHAR NOT NULL,
    last_pr_authored_or_reviewed_at timestamp with time zone,
    is_owner BOOLEAN NOT NULL,
    is_billable BOOLEAN NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    unique(user_id, team_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (team_id) REFERENCES teams(id)
);

-- migrate:down
DROP TABLE IF EXISTS user_teams;