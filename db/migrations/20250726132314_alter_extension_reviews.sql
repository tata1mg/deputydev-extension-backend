-- migrate:up
ALTER TABLE extension_reviews rename to ide_reviews;


-- migrate:down
ALTER TABLE ide_reviews rename to extension_reviews;
