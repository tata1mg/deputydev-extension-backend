-- migrate:up
ALTER TABLE query_summaries
ALTER COLUMN query_id TYPE text
USING query_id::text;

-- migrate:down
ALTER TABLE query_summaries
ALTER COLUMN query_id TYPE integer
USING query_id::integer;
