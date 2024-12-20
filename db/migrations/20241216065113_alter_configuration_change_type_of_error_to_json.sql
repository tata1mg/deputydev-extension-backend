-- migrate:up

update configurations
set error=null
where error = '';

ALTER TABLE configurations
    ALTER COLUMN error TYPE JSONB USING error::jsonb;

-- migrate:down
ALTER TABLE configurations
    ALTER COLUMN error TYPE TEXT USING error::text;
