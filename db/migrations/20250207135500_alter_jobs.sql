-- migrate:up
ALTER TABLE job ADD COLUMN llm_model VARCHAR;
ALTER TABLE job ADD COLUMN loc BIGINT;

UPDATE job
SET llm_model = meta_info->'llm_meta'->0->>'llm_model'
WHERE meta_info IS NOT NULL;

-- migrate:down
ALTER TABLE job DROP COLUMN llm_model;
ALTER TABLE job DROP COLUMN loc;
