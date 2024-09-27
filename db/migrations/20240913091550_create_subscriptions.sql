-- 005_create_subscriptions.sql

-- migrate:up
CREATE TABLE subscriptions (
    id BIGSERIAL PRIMARY KEY,
    plan_id BIGINT NOT NULL,
    team_id BIGINT NOT NULL UNIQUE,
    current_status VARCHAR NOT NULL,
    start_date timestamp with time zone NOT NULL,
    end_date timestamp with time zone,
    billable_type VARCHAR NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (plan_id) REFERENCES subscription_plans(id) ,
    FOREIGN KEY (team_id) REFERENCES teams(id)
);

-- migrate:down
DROP TABLE IF EXISTS subscriptions;
