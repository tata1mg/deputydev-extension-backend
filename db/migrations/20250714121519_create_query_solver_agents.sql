-- migrate:up
CREATE TABLE query_solver_agents
(
    id                        SERIAL PRIMARY KEY,
    name                      TEXT NOT NULL,
    agent_enum                TEXT NOT NULL,
    description               TEXT NOT NULL,
    prompt_intent             TEXT NOT NULL,
    status                    TEXT NOT NULL,
    allowed_first_party_tools JSONB NOT NULL,
    created_at                timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at                timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE UNIQUE INDEX query_solver_agents_agent_enum_idx ON query_solver_agents (agent_enum);

-- migrate:down
drop table query_solver_agents;