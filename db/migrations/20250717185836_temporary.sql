-- migrate:up
alter table user_agents
add column if not exists is_deleted boolean default false;

CREATE UNIQUE INDEX IF NOT EXISTS user_agents_user_team_id_agent_name_unique_active
ON user_agents (user_team_id, agent_name)
WHERE is_deleted = FALSE;

-- migrate:down

