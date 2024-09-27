-- migrate:up
ALTER TABLE pr_comments DROP CONSTRAINT IF EXISTS pr_comments_organisation_id_fkey;
ALTER TABLE pr_comments RENAME organisation_id TO team_id;
ALTER TABLE pr_comments ADD CONSTRAINT pr_comments_team_id_fkey FOREIGN KEY (team_id)
REFERENCES teams(id);

-- migrate:down
ALTER TABLE pr_comments DROP CONSTRAINT IF EXISTS pr_comments_team_id_fkey;
ALTER TABLE pr_comments RENAME team_id TO organisation_id;
ALTER TABLE pr_comments ADD CONSTRAINT pr_comments_organisation_id_fkey FOREIGN KEY (organisation_id)
REFERENCES organisations(id);
