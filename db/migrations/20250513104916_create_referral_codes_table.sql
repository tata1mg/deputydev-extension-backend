-- migrate:up
CREATE TABLE IF NOT EXISTS referral_codes (
    id SERIAL PRIMARY KEY,
    referrer_id BIGINT NOT NULL,
    referral_code VARCHAR NOT NULL,
    benefits JSON NOT NULL,
    current_limit_left INT NOT NULL,
    max_usage_limit INT NOT NULL,
    expiration_date timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- migrate:down
DROP TABLE IF EXISTS referral_codes;

