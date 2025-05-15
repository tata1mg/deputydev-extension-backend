-- migrate:up
CREATE TABLE IF NOT EXISTS referrals (
    id SERIAL PRIMARY KEY,
    referral_code_id BIGINT NOT NULL,
    referree_id BIGINT NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- migrate:down
DROP TABLE IF EXISTS referrals;
