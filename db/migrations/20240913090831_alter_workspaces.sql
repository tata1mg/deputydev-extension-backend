-- migrate:up
ALTER TABLE workspaces DROP CONSTRAINT IF EXISTS workspaces_organisation_id_fkey;
ALTER TABLE workspaces RENAME organisation_id TO team_id;
ALTER TABLE workspaces ADD CONSTRAINT workspaces_team_id_fkey FOREIGN KEY (team_id)
REFERENCES teams(id);
ALTER TABLE workspaces ADD COLUMN integration_id bigint;
ALTER TABLE workspaces ADD CONSTRAINT workspaces_integration_id_fkey FOREIGN KEY (integration_id)
REFERENCES integrations(id);
ALTER TABLE workspaces ADD COLUMN slug VARCHAR;

-- migrate:down
ALTER TABLE workspaces DROP COLUMN slug;
ALTER TABLE workspaces DROP CONSTRAINT IF EXISTS workspaces_integration_id_fkey;
ALTER TABLE workspaces DROP COLUMN integration_id;
ALTER TABLE workspaces DROP CONSTRAINT IF EXISTS workspaces_team_id_fkey;
ALTER TABLE workspaces RENAME team_id TO organisation_id;
ALTER TABLE workspaces ADD CONSTRAINT workspaces_organisation_id_fkey FOREIGN KEY (organisation_id)
REFERENCES organisations(id);
