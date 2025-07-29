-- migrate:up
ALTER TABLE ide_reviews_comments ADD COLUMN title text;
ALTER TABLE extension_reviews ADD COLUMN title text;


-- migrate:down

