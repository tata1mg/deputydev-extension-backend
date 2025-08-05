-- migrate:up
ALTER TABLE ide_reviews_comments
ADD COLUMN comment_status VARCHAR;

-- migrate:down
ALTER TABLE ide_reviews_comments
DROP COLUMN comment_status;