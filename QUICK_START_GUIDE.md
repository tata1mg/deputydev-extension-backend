In order to quickly start, clone these repos in the same folder -
https://github.com/tata1mg/deputydev-auth.git
https://github.com/tata1mg/deputydev-extension-backend.git
https://github.com/tata1mg/deputydev-binary.git
https://github.com/tata1mg/deputydev-vscode-extension.git
https://github.com/tata1mg/deputydev-core.git


Now, run the following in deputydev-auth and deputydev-extension-backend
cp config_template.json config.json
This will create a config file for you for auth and backend. The service depends on redis, localstack, and postgres. These will be set up by the docker compose. The config_template contains creds for these in local setup already put. If you want to change them you can always edit the docker compose and config.json acccordingly.

Now, for 1st time, we will need to run the DB migrations. These are dbmate migrations, and can be run 