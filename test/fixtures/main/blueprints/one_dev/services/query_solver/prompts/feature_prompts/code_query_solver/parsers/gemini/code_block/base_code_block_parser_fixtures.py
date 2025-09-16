from typing import Any, Dict, List


class BaseCodeBlockParserFixtures:
    """Fixture data for base code block parser tests."""

    @staticmethod
    def get_code_block_header(language: str, filepath: str, is_diff: bool) -> str:
        """Generate a code block header with specified parameters."""
        return f"""<programming_language>{language}</programming_language><file_path>{filepath}</file_path><is_diff>{str(is_diff).lower()}</is_diff>
"""

    @staticmethod
    def get_simple_python_code_block() -> str:
        """Get a simple Python code block for testing."""
        return """<programming_language>python</programming_language><file_path>main.py</file_path><is_diff>false</is_diff>
def hello_world():
    print("Hello, World!")
    return "success"

if __name__ == "__main__":
    result = hello_world()
    print(f"Result: {result}")"""

    @staticmethod
    def get_simple_javascript_code_block() -> str:
        """Get a simple JavaScript code block for testing."""
        return """<programming_language>javascript</programming_language><file_path>app.js</file_path><is_diff>false</is_diff>
function greetUser(name) {
    console.log(`Hello, ${name}!`);
    return `Greeting sent to ${name}`;
}

const userName = "World";
const message = greetUser(userName);
console.log(message);"""

    @staticmethod
    def get_javascript_code_parts() -> List[str]:
        """Get JavaScript code split into parts for incremental parsing."""
        return [
            "const express = require('express');\n",
            "const app = express();\n",
            "\n",
            "app.get('/', (req, res) => {\n",
            "    res.json({ message: 'Hello World' });\n",
            "});\n",
            "\n",
            "const PORT = process.env.PORT || 3000;\n",
            "app.listen(PORT, () => {\n",
            "    console.log(`Server running on port ${PORT}`);\n",
            "});",
        ]

    @staticmethod
    def get_simple_diff_example() -> str:
        """Get a simple diff example for testing."""
        return """<programming_language>python</programming_language><file_path>calculator.py</file_path><is_diff>true</is_diff>
@@ -1,4 +1,6 @@
 def add(a, b):
-    return a + b
+    \"\"\"Add two numbers with validation.\"\"\"
+    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
+        raise TypeError("Arguments must be numbers")
+    return a + b
 
 def subtract(a, b):
     return a - b"""

    @staticmethod
    def get_complex_diff_example() -> str:
        """Get a complex diff with multiple hunks."""
        return """<programming_language>python</programming_language><file_path>user_service.py</file_path><is_diff>true</is_diff>
@@ -1,8 +1,12 @@
+import logging
+from typing import Optional, Dict, Any
+
 class UserService:
     def __init__(self):
         self.users = {}
+        self.logger = logging.getLogger(__name__)
     
     def create_user(self, username, email):
-        if username in self.users:
-            return False
+        if not username or not email:
+            raise ValueError("Username and email are required")
+        if username in self.users:
+            self.logger.warning(f"Attempted to create duplicate user: {username}")
+            return False
         
         self.users[username] = {
             'email': email,
@@ -15,6 +19,10 @@
         }
         return True
     
+    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
+        \\\"\\\"\\\"Get user by username.\\\"\\\"\\\"
+        return self.users.get(username)
+    
     def delete_user(self, username):
-        if username in self.users:
-            del self.users[username]
-            return True
-        return False
+        try:
+            del self.users[username]
+            self.logger.info(f"User deleted: {username}")
+            return True
+        except KeyError:
+            self.logger.error(f"Attempted to delete non-existent user: {username}")
+            return False"""

    @staticmethod
    def get_diff_counting_test_cases() -> List[Dict[str, Any]]:
        """Get test cases for diff line counting accuracy."""
        return [
            {
                "diff": """<programming_language>python</programming_language><file_path>test.py</file_path><is_diff>true</is_diff>
@@ -1,3 +1,5 @@
 import os
-import sys
+import sys
+import json
+import logging
 
 def main():
-    print("old version")
+    print("new version")
     return 0""",
                "expected_added": 4,  # +import sys, +import json, +import logging, +print("new version")
                "expected_removed": 2,  # -import sys, -print("old version")
            },
            {
                "diff": """<programming_language>javascript</programming_language><file_path>config.js</file_path><is_diff>true</is_diff>
@@ -1,5 +1,8 @@
 const config = {
     database: {
-        host: 'localhost',
-        port: 3306
+        host: process.env.DB_HOST || 'localhost',
+        port: process.env.DB_PORT || 3306,
+        username: process.env.DB_USER || 'root',
+        password: process.env.DB_PASS || ''
     }
 };""",
                "expected_added": 4,  # 4 new lines added
                "expected_removed": 2,  # 2 lines removed
            },
            {
                "diff": """<programming_language>sql</programming_language><file_path>schema.sql</file_path><is_diff>true</is_diff>
@@ -1,6 +1,10 @@
 CREATE TABLE users (
     id SERIAL PRIMARY KEY,
     username VARCHAR(50) UNIQUE NOT NULL,
-    email VARCHAR(100) NOT NULL
+    email VARCHAR(100) UNIQUE NOT NULL,
+    password_hash VARCHAR(255) NOT NULL,
+    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
+    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
+    is_active BOOLEAN DEFAULT TRUE
 );""",
                "expected_added": 5,  # 5 new lines added (1 modified + 4 new)
                "expected_removed": 1,  # 1 line modified (email line)
            },
        ]

    @staticmethod
    def get_empty_code_block() -> str:
        """Get an empty code block for testing."""
        return """<programming_language>python</programming_language><file_path>empty.py</file_path><is_diff>false</is_diff>"""

    @staticmethod
    def get_malformed_header_examples() -> List[str]:
        """Get malformed header examples for error handling."""
        return [
            # Missing is_diff tag
            """<programming_language>python</programming_language><file_path>test.py</file_path>
print("incomplete header")""",
            # Missing file_path tag
            """<programming_language>javascript</programming_language><is_diff>false</is_diff>
console.log("missing file path");""",
            # Missing programming_language tag
            """<file_path>test.sql</file_path><is_diff>false</is_diff>
SELECT * FROM users;""",
            # Empty tags
            """<programming_language></programming_language><file_path></file_path><is_diff></is_diff>
// empty tags""",
            # Invalid is_diff value
            """<programming_language>python</programming_language><file_path>test.py</file_path><is_diff>maybe</is_diff>
print("invalid is_diff value")""",
            # No XML tags at all
            """def function_without_header():
    return "no header at all\"""",
            # Malformed XML
            """<programming_language>python<file_path>broken.py</file_path><is_diff>false</is_diff>
print("malformed XML")""",
        ]

    @staticmethod
    def get_special_characters_examples() -> List[Dict[str, Any]]:
        """Get examples with special characters for testing."""
        return [
            {
                "content": """<programming_language>python</programming_language><file_path>src/utils/special-chars.py</file_path><is_diff>false</is_diff>
# File with special characters in path and content
def process_unicode():
    text = "Hello 世界! 🌍 Testing éñçødīñg"
    return text""",
                "expected_path": "src/utils/special-chars.py",
            },
            {
                "content": """<programming_language>javascript</programming_language><file_path>tests/unit/test_file_parser.js</file_path><is_diff>false</is_diff>
// Testing underscores and special chars
describe('File Parser', () => {
    it('should handle special characters: àáâãäåæç', () => {
        expect(true).toBe(true);
    });
});""",
                "expected_path": "tests/unit/test_file_parser.js",
            },
            {
                "content": """<programming_language>sql</programming_language><file_path>migrations/001_create_users_table.sql</file_path><is_diff>false</is_diff>
-- SQL with special characters
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) CHECK (name ~ '^[A-Za-z\\s\\-\\']+$'),
    email VARCHAR(255) UNIQUE NOT NULL
);""",
                "expected_path": "migrations/001_create_users_table.sql",
            },
        ]

    @staticmethod
    def get_large_code_example() -> str:
        """Get a large code example for performance testing."""
        return """<programming_language>python</programming_language><file_path>large_file.py</file_path><is_diff>false</is_diff>
\"\"\"
Large code file for performance testing.
This file contains multiple classes and functions to test parser performance.
\"\"\"

import os
import sys
import json
import logging
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, timedelta
from pathlib import Path


class ConfigurationManager:
    \"\"\"Manages application configuration with environment variables and file-based config.\"\"\"
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or os.getenv('CONFIG_PATH', 'config.json')
        self.config_data = {}
        self.logger = logging.getLogger(__name__)
        self.load_configuration()
    
    def load_configuration(self) -> None:
        \"\"\"Load configuration from file and environment variables.\"\"\"
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config_data = json.load(f)
                self.logger.info(f"Loaded configuration from {self.config_path}")
            else:
                self.logger.warning(f"Configuration file not found: {self.config_path}")
                
            # Override with environment variables
            self._load_env_overrides()
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _load_env_overrides(self) -> None:
        \"\"\"Load environment variable overrides.\"\"\"
        env_mappings = {
            'DATABASE_URL': 'database.url',
            'REDIS_URL': 'redis.url',
            'LOG_LEVEL': 'logging.level',
            'DEBUG': 'debug',
            'SECRET_KEY': 'security.secret_key'
        }
        
        for env_var, config_key in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                self._set_nested_config(config_key, env_value)
    
    def _set_nested_config(self, key_path: str, value: Any) -> None:
        \"\"\"Set a nested configuration value using dot notation.\"\"\"
        keys = key_path.split('.')
        current = self.config_data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        \"\"\"Get a configuration value using dot notation.\"\"\"
        keys = key_path.split('.')
        current = self.config_data
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default


class DatabaseManager:
    \"\"\"Database connection and query management.\"\"\"
    
    def __init__(self, config_manager: ConfigurationManager):
        self.config = config_manager
        self.connection = None
        self.logger = logging.getLogger(__name__)
        self.connection_pool = []
        self.max_connections = self.config.get('database.max_connections', 10)
    
    def connect(self) -> bool:
        \"\"\"Establish database connection.\"\"\"
        try:
            db_url = self.config.get('database.url')
            if not db_url:
                raise ValueError("Database URL not configured")
            
            # Simulate database connection
            self.connection = f"Connected to {db_url}"
            self.logger.info("Database connection established")
            return True
            
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            return False
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        \"\"\"Execute a database query with parameters.\"\"\"
        if not self.connection:
            raise RuntimeError("Database not connected")
        
        # Simulate query execution
        self.logger.debug(f"Executing query: {query[:100]}...")
        
        # Mock result
        return [
            {"id": 1, "name": "Test User", "created_at": datetime.now().isoformat()},
            {"id": 2, "name": "Another User", "created_at": datetime.now().isoformat()}
        ]
    
    def close(self) -> None:
        \"\"\"Close database connection.\"\"\"
        if self.connection:
            self.connection = None
            self.logger.info("Database connection closed")


class CacheManager:
    \"\"\"In-memory cache with TTL support.\"\"\"
    
    def __init__(self, default_ttl: int = 3600):
        self.cache = {}
        self.ttl_data = {}
        self.default_ttl = default_ttl
        self.logger = logging.getLogger(__name__)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        \"\"\"Set a cache value with optional TTL.\"\"\"
        ttl = ttl or self.default_ttl
        expiry_time = datetime.now() + timedelta(seconds=ttl)
        
        self.cache[key] = value
        self.ttl_data[key] = expiry_time
        
        self.logger.debug(f"Cache set: {key} (expires: {expiry_time})")
    
    def get(self, key: str) -> Optional[Any]:
        \"\"\"Get a cache value, checking TTL.\"\"\"
        if key not in self.cache:
            return None
        
        if datetime.now() > self.ttl_data[key]:
            # Expired
            del self.cache[key]
            del self.ttl_data[key]
            self.logger.debug(f"Cache expired: {key}")
            return None
        
        self.logger.debug(f"Cache hit: {key}")
        return self.cache[key]
    
    def delete(self, key: str) -> bool:
        \"\"\"Delete a cache entry.\"\"\"
        if key in self.cache:
            del self.cache[key]
            del self.ttl_data[key]
            self.logger.debug(f"Cache deleted: {key}")
            return True
        return False
    
    def clear(self) -> None:
        \"\"\"Clear all cache entries.\"\"\"
        self.cache.clear()
        self.ttl_data.clear()
        self.logger.info("Cache cleared")


class ApplicationService:
    \"\"\"Main application service orchestrating all components.\"\"\"
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_manager = ConfigurationManager(config_path)
        self.database_manager = DatabaseManager(self.config_manager)
        self.cache_manager = CacheManager()
        self.logger = logging.getLogger(__name__)
        self.is_running = False
    
    def initialize(self) -> bool:
        \"\"\"Initialize all application components.\"\"\"
        try:
            # Setup logging
            log_level = self.config_manager.get('logging.level', 'INFO')
            logging.basicConfig(level=getattr(logging, log_level.upper()))
            
            # Connect to database
            if not self.database_manager.connect():
                return False
            
            self.logger.info("Application initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Application initialization failed: {e}")
            return False
    
    def start(self) -> None:
        \"\"\"Start the application service.\"\"\"
        if not self.initialize():
            raise Runtimeerror("Failed to initialize application")
        
        self.is_running = True
        self.logger.info("Application service started")
    
    def stop(self) -> None:
        \"\"\"Stop the application service.\"\"\"
        self.is_running = False
        self.database_manager.close()
        self.cache_manager.clear()
        self.logger.info("Application service stopped")
    
    def health_check(self) -> Dict[str, Any]:
        \"\"\"Perform application health check.\"\"\"
        return {
            "status": "healthy" if self.is_running else "stopped",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "database": bool(self.database_manager.connection),
                "cache": len(self.cache_manager.cache),
                "config": bool(self.config_manager.config_data)
            }
        }


def main():
    \"\"\"Main entry point for the application.\"\"\"
    app_service = ApplicationService()
    
    try:
        app_service.start()
        
        # Example operations
        health = app_service.health_check()
        print(f"Health check: {health}")
        
        # Cache some data
        app_service.cache_manager.set("test_key", {"message": "Hello, World!"})
        cached_data = app_service.cache_manager.get("test_key")
        print(f"Cached data: {cached_data}")
        
        # Execute a query
        results = app_service.database_manager.execute_query("SELECT * FROM users")
        print(f"Query results: {results}")
        
    except Exception as e:
        print(f"Application error: {e}")
    finally:
        app_service.stop()


if __name__ == "__main__":
    main()"""

    @staticmethod
    def get_mixed_content_examples() -> List[str]:
        """Get mixed content examples for comprehensive testing."""
        return [
            # Valid Python code block
            """<programming_language>python</programming_language><file_path>mixed_test.py</file_path><is_diff>false</is_diff>
def mixed_function():
    return "This is a mixed content test"

# Some comment with special chars: àáâãäå
print(mixed_function())""",
            # Valid diff
            """<programming_language>javascript</programming_language><file_path>app.js</file_path><is_diff>true</is_diff>
@@ -1,3 +1,5 @@
 const express = require('express');
+const cors = require('cors');
 const app = express();

+app.use(cors());
 app.listen(3000);""",
            # Mixed with unusual formatting
            """<programming_language>css</programming_language><file_path>styles.css</file_path><is_diff>false</is_diff>
/* CSS with various selectors and properties */
.container {
    display: flex;
    justify-content: center;
    align-items: center;
}

@media (max-width: 768px) {
    .container {
        flex-direction: column;
    }
}""",
            # TypeScript with generics
            """<programming_language>typescript</programming_language><file_path>utils.ts</file_path><is_diff>false</is_diff>
interface ApiResponse<T> {
    data: T;
    status: number;
    message: string;
}

function processResponse<T>(response: ApiResponse<T>): T {
    if (response.status === 200) {
        return response.data;
    }
    throw new Error(response.message);
}""",
            # Complex diff with multiple file types
            """<programming_language>yaml</programming_language><file_path>docker-compose.yml</file_path><is_diff>true</is_diff>
@@ -1,8 +1,12 @@
 version: '3.8'
 services:
   web:
     build: .
-    ports:
-      - "3000:3000"
+    ports:
+      - "3000:3000"
+    environment:
+      - NODE_ENV=production
+  db:
+    image: postgres:13
+    environment:
+      - POSTGRES_DB=myapp""",
        ]
