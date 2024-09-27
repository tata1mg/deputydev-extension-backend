-- migrate:up
ALTER TABLE pull_requests DROP CONSTRAINT IF EXISTS pull_requests_organisation_id_fkey;
DROP INDEX IF EXISTS pull_requests_organisation_id_created_scm_idx;
ALTER TABLE pull_requests RENAME organisation_id TO team_id;
ALTER TABLE pull_requests ADD CONSTRAINT pull_requests_team_id_fkey FOREIGN KEY (team_id)
REFERENCES teams(id);
CREATE INDEX IF NOT EXISTS pull_requests_team_id_created_scm_idx ON pull_requests(team_id, created_at, scm);

-- migrate:down
DROP INDEX IF EXISTS pull_requests_team_id_created_scm_idx;
ALTER TABLE pull_requests DROP CONSTRAINT IF EXISTS pull_requests_team_id_fkey;
ALTER TABLE pull_requests RENAME team_id TO organisation_id;
CREATE INDEX IF NOT EXISTS pull_requests_organisation_id_created_scm_idx ON pull_requests(organisation_id, created_at, scm);
ALTER TABLE pull_requests ADD CONSTRAINT pull_requests_organisation_id_fkey FOREIGN KEY (organisation_id)
REFERENCES organisations(id);
