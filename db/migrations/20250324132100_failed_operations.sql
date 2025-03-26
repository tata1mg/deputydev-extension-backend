-- migrate:up
create table if not exists failed_operations (
    id serial primary key,
    type TEXT NOT NULL,
    data jsonb not null,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- migrate:down
drop table if exists failed_operations;