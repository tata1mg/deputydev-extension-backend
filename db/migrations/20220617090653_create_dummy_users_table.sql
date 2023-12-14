-- migrate:up
create table dummy_users (
  id integer,
  name varchar(255),
  email varchar(255) not null
);

-- migrate:down
drop table dummy_users;