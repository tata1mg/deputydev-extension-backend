-- migrate:up
CREATE TABLE IF NOT EXISTS job_feedbacks (
    id SERIAL PRIMARY KEY,
    job_id INT NOT NULL,
    feedback VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_job_feedbacks_job_id ON job_feedbacks(job_id);


-- migrate:down
DROP INDEX IF EXISTS idx_job_feedbacks_job_id;
DROP TABLE IF EXISTS job_feedbacks;
