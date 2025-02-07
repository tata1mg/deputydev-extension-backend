-- migrate:up
ALTER TABLE job ADD COLUMN llm_model VARCHAR;
ALTER TABLE job ADD COLUMN code_lines_count BIGINT;

UPDATE job
SET llm_model = meta_info->'llm_meta'->0->>'llm_model'
WHERE meta_info IS NOT NULL;

-- migrate:down
UPDATE job
SET meta_info = jsonb_set(
    COALESCE(meta_info::jsonb, '{}'::jsonb),  -- Ensure correct casting
    '{llm_meta,0,llm_model}',
    to_jsonb(llm_model)
)
WHERE meta_info IS NOT NULL AND llm_model IS NOT NULL;

ALTER TABLE job DROP COLUMN code_lines_count;
ALTER TABLE job DROP COLUMN llm_model;
