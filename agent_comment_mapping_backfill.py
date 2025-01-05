# TODO: Need to test
import psycopg2
from psycopg2 import sql

# Database connection settings
db_config = {
    "dbname": "your_db_name",
    "user": "your_username",
    "password": "your_password",
    "host": "your_host",
    "port": "your_port",
}

BATCH_SIZE = 1000  # Number of records to process in each batch

try:
    # Connect to the database
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    # Mapping of bucket_name to agent_name (assuming it's still needed for validation)
    bucket_to_agent_mapping = {
        "bucket1": "agent1",
        "bucket2": "agent2",
        # Add more mappings as required
    }

    # Step: Insert into agents_comment_mapping table in batches
    for bucket_name, agent_name in bucket_to_agent_mapping.items():
        cursor.execute(
            """
            SELECT a.id, bcm.pr_comment_id
            FROM buckets b
            JOIN bucket_comment_mapping bcm ON b.id = bcm.bucket_id
            JOIN pr_comments pc ON bcm.pr_comment_id = pc.id
            JOIN agents a ON a.name = %s AND a.repo_id = pc.repo_id
            WHERE b.name = %s;
            """,
            (agent_name, bucket_name),
        )

        records = cursor.fetchall()
        for i in range(0, len(records), BATCH_SIZE):
            batch = records[i : i + BATCH_SIZE]
            insert_query = """
                INSERT INTO agents_comment_mapping (agent_id, pr_comment_id)
                VALUES %s;
            """
            psycopg2.extras.execute_values(cursor, insert_query, batch, template="(%s, %s)")

    # Commit the transaction
    conn.commit()
    print("Data migration for agents_comment_mapping completed successfully.")

except Exception as e:
    # Rollback in case of error
    if conn:
        conn.rollback()
    print(f"Error: {e}")

finally:
    # Close the connection
    if cursor:
        cursor.close()
    if conn:
        conn.close()
