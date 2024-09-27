-- migrate:up
ALTER TABLE feedbacks DROP CONSTRAINT IF EXISTS feedbacks_organisation_id_fkey;
ALTER TABLE feedbacks RENAME organisation_id TO team_id;
ALTER TABLE feedbacks ADD CONSTRAINT feedbacks_team_id_fkey FOREIGN KEY (team_id)
REFERENCES teams(id);

-- migrate:down
ALTER TABLE feedbacks DROP CONSTRAINT IF EXISTS feedbacks_team_id_fkey;
ALTER TABLE feedbacks RENAME team_id TO organisation_id;
ALTER TABLE feedbacks ADD CONSTRAINT feedbacks_organisation_id_fkey FOREIGN KEY (organisation_id)
REFERENCES organisations(id);
