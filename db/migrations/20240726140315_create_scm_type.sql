-- migrate:up
CREATE TYPE scm_type AS ENUM (
    'bitbucket',
    'github',
    'gitlab'
);

-- migrate:down
DROP TYPE IF EXISTS scm_type;
