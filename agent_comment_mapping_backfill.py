import psycopg2
from psycopg2 import sql

# Database connection settings
db_config = {
    "dbname": "mars_deputydev_db",
    "user": "mars_deputydev_user",
    "password": "mars_deputydev_pass",
    "host": "marspostgres14.1mginfra.com",
    "port": 5432,
}

BATCH_SIZE = 500  # Number of records to process in each batch

try:
    # Connect to the database
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    # Mapping of bucket_name to agent_name (assuming it's still needed for validation)
    bucket_to_agent_mapping = {
        "SECURITY": "security",
        "MAINTAINABILITY": "code_maintainability",
        "USER_STORY": "business_validation_agent",
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
        "FEATURE": "business_validation_agent",
        "INFO": "code_communication",
        "ACCESSIBILITY": "business_validation_agent",
        "BUSINESS_LOGIC": "business_validation_agent",
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
        "LAYOUT": "business_validation_agent",
        "RESOLVED": "code_communication",
        "VISUAL": "business_validation_agent",
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
        "UI": "business_validation_agent",
        "TEST_QUALITY": "code_maintainability",
        "SEMANTICERROR": "error",
        "CONFIG": "code_maintainability",
        "LOCALIZATION": "business_validation_agent",
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
        "USER_EXPERIENCE": "business_validation_agent",
        "BREAKING_CHANGE": "error",
        "CONFIGURATION_UPDATE": "code_communication",
        "NO_ERROR": "code_communication",
        "CLEAN_CODE": "code_maintainability",
        "COMPATIBILITY": "error",
    }

    # Step: Insert into agents_comment_mapping table in batches
    for bucket_name, agent_name in bucket_to_agent_mapping.items():
        cursor.execute(
            """
            SELECT a.id, cbm.pr_comment_id
            FROM buckets b
            JOIN comment_bucket_mapping cbm ON b.id = cbm.bucket_id
            JOIN pr_comments pc ON cbm.pr_comment_id = pc.id
            JOIN agents a ON a.agent_name = %s AND a.repo_id = pc.repo_id
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
