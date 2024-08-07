-- migrate:up
ALTER TABLE pull_requests ADD pr_state varchar;
ALTER TABLE pull_requests RENAME scm_merge_time TO scm_close_time;

-- migrate:down
ALTER TABLE pull_requests DROP COLUMN pr_state;
ALTER TABLE pull_requests RENAME scm_close_time TO scm_merge_time;