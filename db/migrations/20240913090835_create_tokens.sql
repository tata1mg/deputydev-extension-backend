-- migrate:up
CREATE TABLE tokens (
    id BIGSERIAL PRIMARY KEY,
    token VARCHAR NOT NULL,
    type VARCHAR NOT NULL,
    tokenable_type VARCHAR NOT NULL,
    tokenable_id BIGINT NOT NULL,
    expire_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE(tokenable_type, tokenable_id, type)
);

-- migrate:down
DROP TABLE IF EXISTS tokens;