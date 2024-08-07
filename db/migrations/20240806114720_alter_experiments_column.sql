-- migrate:up
ALTER TABLE experiments ADD pr_state varchar;
ALTER TABLE experiments RENAME scm_merge_time TO scm_close_time;
ALTER TABLE experiments RENAME merge_time_in_sec TO close_time_in_sec;

-- migrate:down
ALTER TABLE experiments DROP COLUMN pr_state;
ALTER TABLE experiments RENAME scm_close_time TO scm_merge_time;
ALTER TABLE experiments RENAME close_time_in_sec TO merge_time_in_sec;