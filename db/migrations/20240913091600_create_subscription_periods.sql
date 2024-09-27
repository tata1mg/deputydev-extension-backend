-- migrate:up
CREATE TABLE subscription_periods (
    id BIGSERIAL PRIMARY KEY,
    subscription_id BIGINT NOT NULL,
    period_start timestamp with time zone NOT NULL,
    period_end timestamp with time zone NOT NULL,
    period_status VARCHAR NOT NULL,
    billing_status VARCHAR NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) 
);

-- migrate:down
DROP TABLE IF EXISTS subscription_periods;
