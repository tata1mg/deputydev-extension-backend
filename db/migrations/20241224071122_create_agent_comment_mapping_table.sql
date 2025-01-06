-- migrate:up
CREATE TABLE agent_comment_mappings
(
    id            BIGSERIAL PRIMARY KEY,
    agent_id      BIGINT                                             NOT NULL REFERENCES agents (id),
    pr_comment_id BIGINT                                             NOT NULL REFERENCES pr_comments (id),
    weight        INT                                                NOT NULL,
    created_at    timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at    timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE (agent_id, pr_comment_id)
);

CREATE INDEX agent_comment_mappings_agent_id ON agent_comment_mappings (agent_id);
CREATE INDEX agent_comment_mappings_comment_id ON agent_comment_mappings (pr_comment_id);
-- migrate:down
drop table agent_comment_mappings;

