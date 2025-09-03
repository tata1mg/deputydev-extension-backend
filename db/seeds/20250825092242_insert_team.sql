-- migrate:up
insert into teams(id, name, llm_model) values (1, 'dummyteam', NULL);

-- migrate:down
delete from teams where name = 'dummyteam';


