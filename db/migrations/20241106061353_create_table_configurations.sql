-- migrate:up
CREATE TYPE configurable_type_enum AS ENUM ('team', 'repo');
CREATE TABLE configurations
(
    id                BIGSERIAL PRIMARY KEY,
    configurable_id   BIGINT                                             NOT NULL,
    configurable_type configurable_type_enum,
    configuration     jsonb,
    error             text,
    created_at        timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at        timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);
CREATE UNIQUE INDEX configurations_configurable_id_type_idx
    ON configurations (configurable_id, configurable_type);

-- migrate:down
DROP INDEX IF EXISTS configurations_configurable_id_type_idx;
drop table configurations;
drop type configurable_type_enum;
