-- migrate:up
create table if not exists failed_kafka_messages (
    id serial primary key,
    message_data jsonb not null,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- migrate:down
drop table if exists failed_kafka_messages;