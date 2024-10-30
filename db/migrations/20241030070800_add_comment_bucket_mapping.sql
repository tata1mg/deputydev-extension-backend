-- migrate:up

-- Step 1: Create the comment_bucket_mapping table if it doesn't exist
CREATE TABLE IF NOT EXISTS comment_bucket_mapping (
    id BIGSERIAL PRIMARY KEY,
    pr_comment_id BIGINT NOT NULL,
    bucket_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (pr_comment_id) REFERENCES pr_comments(id),
    FOREIGN KEY (bucket_id) REFERENCES buckets(id)
);

-- Step 2: Insert existing data into comment_bucket_mapping
INSERT INTO comment_bucket_mapping (pr_comment_id, bucket_id)
SELECT id, bucket_id
FROM pr_comments
WHERE bucket_id IS NOT NULL;

-- Step 3: Drop the foreign key constraint for bucket_id
ALTER TABLE pr_comments
DROP CONSTRAINT IF EXISTS pr_comments_bucket_id_fkey;

-- Step 4: Drop the bucket_id column from pr_comments
ALTER TABLE pr_comments
DROP COLUMN IF EXISTS bucket_id;


-- migrate:down
ALTER TABLE pr_comments
ADD COLUMN bucket_id INTEGER NOT NULL;

ALTER TABLE pr_comments
ADD CONSTRAINT pr_comments_bucket_id_fkey FOREIGN KEY (bucket_id)
REFERENCES buckets(id);

UPDATE pr_comments
SET bucket_id = cbm.bucket_id
FROM comment_bucket_mapping cbm
WHERE pr_comments.id = cbm.pr_comment_id;


DROP TABLE IF EXISTS comment_bucket_mapping;
