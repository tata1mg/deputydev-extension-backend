-- migrate:up
insert into organisations(name, status, email) values ('tata1mg', 'active', 'root@1mg.com');

-- migrate:down
delete from organisations where name = 'tata1mg';
