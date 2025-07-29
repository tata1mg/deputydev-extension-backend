-- migrate:up
ALTER TABLE ide_reviews add column if not exists review_type TEXT;

-- migrate:down
ALTER TABLE ide_reviews drop column review_type;
