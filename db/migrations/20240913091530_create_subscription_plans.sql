-- migrate:up
CREATE TABLE subscription_plans (
    id SERIAL PRIMARY KEY,
    plan_type VARCHAR NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- migrate:down
DROP TABLE IF EXISTS subscription_plans;