import sys
from contextlib import contextmanager
from typing import List, Tuple

import psycopg2
import psycopg2.extras

# Database connection settings
db_config = {
    "dbname": "deputydev_db",
    "user": "deputydev_user",
    "password": "***REMOVED***",
    "host": "deputydev-postgres.1mginfra.com",
    "port": 5432,
}

BATCH_SIZE = 500  # Number of records to process in each batch
BUCKET_TO_AGENT_MAPPING = {
    "SECURITY": "security",
    "MAINTAINABILITY": "code_maintainability",
    "USER_STORY": "business_logic_validation",
    "CODE_QUALITY": "code_maintainability",
    "CODE_ROBUSTNESS": "code_maintainability",
    "RUNTIME_ERROR": "error",
    "SEMANTIC": "error",
    "PERFORMANCE": "performance_optimisation",
    "ERROR": "error",
    "READABILITY": "code_maintainability",
    "RUNTIME": "error",
    "SEMANTIC_ERROR": "error",
    "DOCSTRING": "code_communication",
    "REUSABILITY": "code_maintainability",
    "DATABASE_PERFORMANCE": "performance_optimisation",
    "ALGORITHM_EFFICIENCY": "performance_optimisation",
    "ARCHITECTURE": "code_maintainability",
    "LOGICAL_ERROR": "error",
    "LOGICAL": "error",
    "EDGE_CASE": "code_maintainability",
    "SYNTAX": "code_maintainability",
    "DOCUMENTATION": "code_communication",
    "{ERROR}": "error",
    "LOGGING": "code_communication",
    "IMPROVEMENT": "code_maintainability",
    "SYNTAX_ERROR": "error",
    "EDGE_CASES": "code_maintainability",
    "TESTING": "code_maintainability",
    "CLEANUP": "code_maintainability",
    "{SECURITY}": "security",
    "ENHANCEMENT": "code_maintainability",
    "FEATURE": "business_logic_validation",
    "INFO": "code_communication",
    "ACCESSIBILITY": "business_logic_validation",
    "BUSINESS_LOGIC": "business_logic_validation",
    "STYLE": "code_maintainability",
    "DEPENDENCIES": "code_maintainability",
    "LOGIC": "error",
    "LOGIC_ERROR": "error",
    "REMOVED": "code_communication",
    "OPTIMIZATION": "performance_optimisation",
    "ERROR_HANDLING": "error",
    "API_CHANGE": "error",
    "VALID_IMPLEMENTATION": "code_maintainability",
    "REFACTOR": "code_maintainability",
    "INFORMATIONAL": "code_communication",
    "RESOURCE_MANAGEMENT": "performance_optimisation",
    "BEST_PRACTICE": "code_maintainability",
    "VALID": "code_maintainability",
    "LAYOUT": "business_logic_validation",
    "RESOLVED": "code_communication",
    "VISUAL": "business_logic_validation",
    "WARNING": "code_communication",
    "BEST_PRACTICES": "code_maintainability",
    "CODE ROBUSTNESS": "code_maintainability",
    "RUNTIMEERROR": "error",
    "CODE COMMUNICATION": "code_communication",
    "CONFIGURATION": "code_maintainability",
    "DEPENDENCY": "code_maintainability",
    "CORRECT_IMPLEMENTATION": "code_maintainability",
    "{INFO}": "code_communication",
    "SECURITY_ERROR": "security",
    "{RUNTIME_ERROR}": "error",
    "RUNTIME_ERRORS": "error",
    "NAMING_CONVENTIONS": "code_maintainability",
    "SEMANTIC ERROR": "error",
    "SECURITY_-_ALWAYS_THIS_VALUE_SINCE_ITS_A_SECURITY_AGENT": "security",
    "UNUSED_CODE": "code_maintainability",
    "UI": "business_logic_validation",
    "TEST_QUALITY": "code_maintainability",
    "SEMANTICERROR": "error",
    "CONFIG": "code_maintainability",
    "LOCALIZATION": "business_logic_validation",
    "CORRECT": "code_maintainability",
    "TYPE_SAFETY": "code_maintainability",
    "CODE_STYLE": "code_maintainability",
    "IMPACT": "code_maintainability",
    "DEPENDENCY_UPDATE": "code_maintainability",
    "TODO": "code_communication",
    "MAINTENANCE": "code_maintainability",
    "CONFIGURATION_ERROR": "error",
    "RUNTIME ERROR": "error",
    "UNUSED_VARIABLE": "code_maintainability",
    "SEMANTIC_ERRORS": "error",
    "ALGORITHMIC_EFFICIENCY": "performance_optimisation",
    "COMMENT": "code_communication",
    "USER_EXPERIENCE": "business_logic_validation",
    "BREAKING_CHANGE": "error",
    "CONFIGURATION_UPDATE": "code_communication",
    "NO_ERROR": "code_communication",
    "CLEAN_CODE": "code_maintainability",
    "COMPATIBILITY": "error",
    "{SEMANTIC}": "error",
    "{NO_ISSUE}": "code_communication",
    "UNNECESSARY": "code_maintainability",
    "GENERAL": "code_communication",
    "{IMPROVEMENT}": "code_maintainability",
    "PERFORMANCE_ERROR": "performance_optimisation",
}

AGENT_WEIGHT_MAPPING = {
    "security": 5,
    "error": 5,
    "code_maintainability": 3,
    "code_communication": 1,
    "business_logic_validation": 5,
    "performance_optimisation": 3,
}


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = None
    try:
        conn = psycopg2.connect(**db_config)
        yield conn
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()
            print("Database connection closed")


def fetch_records(cursor, agent_name: str, bucket_name: str) -> List[Tuple]:
    """Fetch records for a given agent and bucket."""
    # Get the weight for the agent
    weight = AGENT_WEIGHT_MAPPING.get(agent_name, 1)  # Default weight of 1 if not found

    query = """
        SELECT a.id, cbm.pr_comment_id, %s as weight
        FROM buckets b
        JOIN comment_bucket_mapping cbm ON b.id = cbm.bucket_id
        JOIN pr_comments pc ON cbm.pr_comment_id = pc.id
        JOIN agents a ON a.agent_name = %s AND a.repo_id = pc.repo_id
        WHERE b.name = %s;
    """
    cursor.execute(query, (weight, agent_name, bucket_name))
    return cursor.fetchall()


def insert_batch(cursor, batch: List[Tuple]):
    """Insert a batch of records into agents_comment_mapping."""
    insert_query = """
        INSERT INTO agent_comment_mappings (agent_id, pr_comment_id, weight)
        VALUES %s
        ON CONFLICT (agent_id, pr_comment_id) 
        DO UPDATE SET weight = EXCLUDED.weight;
    """
    psycopg2.extras.execute_values(cursor, insert_query, batch, template="(%s, %s, %s)")


def migrate_data():
    """Main migration function."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                total_records = 0

                for bucket_name, agent_name in BUCKET_TO_AGENT_MAPPING.items():
                    print(f"Processing bucket: {bucket_name} for agent: {agent_name}")

                    records = fetch_records(cursor, agent_name, bucket_name)
                    batch_count = 0

                    for i in range(0, len(records), BATCH_SIZE):
                        batch = records[i : i + BATCH_SIZE]
                        insert_batch(cursor, batch)
                        batch_count += 1
                        total_records += len(batch)

                        if batch_count % 10 == 0:  # Log progress every 10 batches
                            print(f"Processed {batch_count} batches ({total_records} records)")

                    print(f"Completed {bucket_name}: {len(records)} records processed")

                conn.commit()
                print(f"Migration completed successfully. Total records: {total_records}")

    except Exception as e:
        print(f"Migration failed: {e}")
        raise


if __name__ == "__main__":
    try:
        migrate_data()
    except Exception as e:
        print(f"Script failed: {e}")
        sys.exit(1)
