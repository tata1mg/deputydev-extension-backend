-- migrate:up
insert into teams(id, name, llm_model) values (1, 'tata1mg', NULL);

-- migrate:down
delete from teams where name = 'tata1mg';
