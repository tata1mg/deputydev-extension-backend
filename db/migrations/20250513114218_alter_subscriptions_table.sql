-- migrate:up
ALTER TABLE subscriptions DROP COLUMN billable_type;
ALTER TABLE subscriptions RENAME team_id TO user_team_id;
ALTER TABLE subscriptions
    DROP CONSTRAINT subscriptions_team_id_fkey,
    ADD CONSTRAINT subscriptions_user_team_id_fkey
    FOREIGN KEY (user_team_id) REFERENCES user_teams(id);
-- migrate:down
ALTER TABLE subscriptions RENAME user_team_id TO team_id;
ALTER TABLE subscriptions ADD COLUMN billable_type VARCHAR NOT NULL;
ALTER TABLE subscriptions
    DROP CONSTRAINT subscriptions_user_team_id_fkey,
    ADD CONSTRAINT subscriptions_team_id_fkey
    FOREIGN KEY (team_id) REFERENCES teams(id);