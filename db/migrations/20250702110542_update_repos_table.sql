-- migrate:up

ALTER TABLE repos
ALTER COLUMN scm_repo_id DROP NOT NULL;

ALTER TABLE repos
ALTER COLUMN workspace_id DROP NOT NULL;

ALTER TABLE repos
ALTER COLUMN scm DROP NOT NULL;

ALTER TABLE repos
ADD COLUMN repo_hash varchar(64);

CREATE INDEX repo_hash_in_repos ON repos (repo_hash);


-- migrate:down
ROP INDEX IF EXISTS repo_hash_in_repos;

ALTER TABLE repos
DROP COLUMN repo_hash;

ALTER TABLE repos
ALTER COLUMN workspace_id SET NOT NULL;

ALTER TABLE repos
ALTER COLUMN scm_repo_id SET NOT NULL;
