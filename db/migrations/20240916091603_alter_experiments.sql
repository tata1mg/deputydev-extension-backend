-- migrate:up
ALTER TABLE experiments DROP CONSTRAINT IF EXISTS experiments_organisation_id_fkey;
ALTER TABLE experiments RENAME organisation_id TO team_id;
ALTER TABLE experiments ADD CONSTRAINT experiments_team_id_fkey FOREIGN KEY (team_id)
REFERENCES teams(id);

-- migrate:down
ALTER TABLE experiments DROP CONSTRAINT IF EXISTS experiments_team_id_fkey;
ALTER TABLE experiments RENAME team_id TO organisation_id;
ALTER TABLE experiments ADD CONSTRAINT experiments_organisation_id_fkey FOREIGN KEY (organisation_id)
REFERENCES organisations(id);
