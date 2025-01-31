-- migrate:up
delete from job;
alter table job drop column advocacy_id;
alter table job drop column user_email;
alter table job drop column user_name;
alter table job drop column team_id;
alter table job add column user_team_id bigint references user_teams(id) not null;


-- migrate:down
alter table job drop column user_team_id;
alter table job add column advocacy_id int not null;
alter table job add column user_email varchar;
alter table job add column user_name varchar;
alter table job add column team_id int not null;
