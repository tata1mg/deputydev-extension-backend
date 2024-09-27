-- migrate:up
ALTER TABLE repos DROP CONSTRAINT IF EXISTS repos_organisation_id_fkey;
ALTER TABLE repos RENAME organisation_id TO team_id;
ALTER TABLE repos ADD CONSTRAINT repos_team_id_fkey FOREIGN KEY (team_id)
REFERENCES teams(id);

-- migrate:down
ALTER TABLE repos DROP CONSTRAINT IF EXISTS repos_team_id_fkey;
ALTER TABLE repos RENAME team_id TO organisation_id;
ALTER TABLE repos ADD CONSTRAINT repos_organisation_id_fkey FOREIGN KEY (organisation_id)
REFERENCES organisations(id);
