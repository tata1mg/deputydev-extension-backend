![Logo](https://www.google.com/u/0/ac/images/logo.gif?uid=117303872071132793314)

# GenAI Service Setup

## Prerequisite
Before starting the setup process, you should have the following:

1. PostgreSQL and Redis installed on your system

2. Latest version of config.json is required to run the app locally. Contact Vishal Khare<vishal.khare@1mg.com> to get latest version of config.json for running the app locally.

3. Git installed on your system

4. Python 3.9

## Installation

```bash
git clone git@bitbucket.org:tata1mg/zeus.git
```

Setup environment and dependency installation process.
```bash  
cd zeus
pipenv shell
pipenv install
```
Place latest `config.json` in root directory of the project 

## Run Zeus on Local.

```bash 
pipenv -m app.service
```

### Installing pre commit
```
pre-commit install
```
This should create a pre-commit script in `.git` folder


## Run Testcases and generate coverage on Local.

Execute the test cases.
```
pytest
```
Generate Coverage Report.

`Note: Test coverage Should be > 90% before merging any PR into Master`
### Check repo coverage from testcases
```
python -m pytest --cov-report term-missing app/ --cov=app -vvv
```
### Check repo coverage from testcases excluding some files and folders present in .coveragerc file
```
python -m pytest --cov-config=pyproject.toml --cov-report term-missing app/ --cov=app -vvv
```


## Documentation and Other Seeding operations 

Database dump can be downloaded from this link: https://drive.google.com/file/d/1QvG1LFdypB7s3hGRKWcn8TLFuIg8VZYn/view?usp=sharing

More info can be found here - https://1mgtech.atlassian.net/wiki/spaces/MER/pages/2849341449/Reorder+Widget+Revamp+Previously+ordered+items

### Migrations
For migrations, [dbmate](https://github.com/amacneil/dbmate) is used. Steps 
to follow for migration:

- Create a new file `db/migrations` folder:
```
dbmate new test_file_name
```
- Write your migrations like this:
```
    -- migrate:up
    create table dummy_users (
      id integer,
      name varchar(255),
      email varchar(255) not null
    );
  
    -- migrate:down
    drop table dummy_users;
```
migrate:up contains the sql query to be applied, migration down contains the sql query for rollback

### Locally verifying migrations
It's a good idea to locally verify the migrations before pushing the code. To verify 
the migrations, we need to create `.env` file with following content:

```
DATABASE_URL="postgres://test-user@127.0.0.1:5432/test-db?sslmode=disable"
```

Here, `postgres` is the type of db. `127.0.0.1` is the host. `test-user` is the user/role, `127.0.0.1` is the 
`test-db` is the db name. 

To run a migration:
```
dbmate up
```

To rollback a migration:
```
dbmate down
```

Note: Don't push this file into the repository.

### Getting DBMate run on prestage/stage
As per the current process, devops needs to be informed for enabling dbmate for a 
service on an environment through a JIRA ticket. Make sure the code for dbmate is pushed
before getting this enabled on an environment.
