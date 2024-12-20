-- migrate:up
ALTER TABLE pr_comments
    ADD COLUMN weight   INT,
    ADD COLUMN agent_id INT,
    ADD CONSTRAINT fk_agent_id
        FOREIGN KEY (agent_id)
            REFERENCES agents (id);

-- migrate:down
ALTER TABLE pr_comments
    DROP CONSTRAINT IF EXISTS fk_agent_id,
    DROP COLUMN IF EXISTS weight,
    DROP COLUMN IF EXISTS agent_id;
