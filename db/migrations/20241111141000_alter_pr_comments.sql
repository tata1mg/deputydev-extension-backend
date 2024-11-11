-- migrate:up
ALTER TABLE pr_comments
    DROP CONSTRAINT IF EXISTS pr_comments_pr_id_scm_comment_id_key;

ALTER TABLE pr_comments
    ALTER COLUMN scm_comment_id DROP NOT NULL;

DROP INDEX IF EXISTS pr_comments_pr_id_scm_comment_id_key;

CREATE UNIQUE INDEX IF NOT EXISTS pr_comments_pr_id_scm_comment_id_unique
ON pr_comments(pr_id, scm_comment_id)
WHERE scm_comment_id IS NOT NULL;


-- migrate:down

DROP INDEX IF EXISTS pr_comments_pr_id_scm_comment_id_unique;

ALTER TABLE pr_comments
    ALTER COLUMN scm_comment_id SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS pr_comments_pr_id_scm_comment_id_unique
ON pr_comments(pr_id, scm_comment_id);
