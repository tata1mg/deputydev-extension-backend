-- migrate:up

-- Drop old index
DROP INDEX IF EXISTS user_agents_user_team_id_agent_name_unique_active;

-- Create new index on display_name
CREATE UNIQUE INDEX IF NOT EXISTS user_agents_user_team_id_display_name_unique_active
ON user_agents (user_team_id, display_name)
WHERE is_deleted = FALSE;

-- migrate:down

-- Drop new index
DROP INDEX IF EXISTS user_agents_user_team_id_display_name_unique_active;

-- Restore old index
CREATE UNIQUE INDEX IF NOT EXISTS user_agents_user_team_id_agent_name_unique_active
ON user_agents (user_team_id, agent_name)
WHERE is_deleted = FALSE;