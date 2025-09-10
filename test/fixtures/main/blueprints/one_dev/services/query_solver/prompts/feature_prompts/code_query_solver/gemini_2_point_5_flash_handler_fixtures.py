from typing import Any, Dict, List
from app.backend_common.models.dto.message_thread_dto import (
    ContentBlockCategory,
    MessageData,
    TextBlockContent,
    TextBlockData,
)


class Gemini2Point5FlashHandlerFixtures:
    """Fixture data for Gemini 2.5 Flash Handler tests."""

    @staticmethod
    def get_sample_params() -> Dict[str, Any]:
        """Get sample parameters for handler initialization."""
        return {
            "query": "Write a Python function to calculate factorial",
            "files": [
                {
                    "path": "src/main.py",
                    "content": "# Main application file\nprint('Hello World')",
                },
                {
                    "path": "src/utils.py", 
                    "content": "# Utility functions\ndef helper():\n    pass",
                }
            ],
            "additional_context": "Use recursive approach and include error handling",
            "repository_structure": {
                "src": ["main.py", "utils.py", "models.py"],
                "tests": ["test_main.py", "test_utils.py"],
                "docs": ["README.md", "API.md"]
            },
            "session_context": "Previous conversation about implementing mathematical functions",
        }

    @staticmethod
    def get_minimal_params() -> Dict[str, Any]:
        """Get minimal parameters for handler initialization."""
        return {
            "query": "Simple query",
            "files": [],
        }

    @staticmethod
    def get_complex_params() -> Dict[str, Any]:
        """Get complex parameters for comprehensive testing."""
        return {
            "query": "Implement a complete REST API with authentication, database models, and unit tests",
            "files": [
                {
                    "path": "app/models/user.py",
                    "content": "from sqlalchemy import Column, Integer, String\n\nclass User(Base):\n    id = Column(Integer, primary_key=True)",
                },
                {
                    "path": "app/api/auth.py",
                    "content": "from flask import Blueprint\n\nauth_bp = Blueprint('auth', __name__)",
                },
                {
                    "path": "tests/test_auth.py",
                    "content": "import pytest\n\ndef test_login():\n    pass",
                }
            ],
            "additional_context": "Use Flask framework with SQLAlchemy ORM. Follow RESTful conventions.",
            "repository_structure": {
                "app": ["__init__.py", "models", "api", "services"],
                "app/models": ["user.py", "auth.py", "base.py"],
                "app/api": ["auth.py", "users.py", "common.py"],
                "app/services": ["auth_service.py", "user_service.py"],
                "tests": ["test_auth.py", "test_users.py", "conftest.py"],
                "config": ["settings.py", "database.py"],
                "requirements": ["requirements.txt", "requirements-dev.txt"]
            },
            "session_context": "Building a microservice for user management with JWT authentication",
            "technical_requirements": {
                "framework": "Flask",
                "database": "PostgreSQL",
                "authentication": "JWT",
                "testing": "pytest"
            }
        }

    @staticmethod
    def get_sample_message_data() -> List[MessageData]:
        """Get sample message data for testing response parsing."""
        return [
            TextBlockData(
                type=ContentBlockCategory.TEXT_BLOCK,
                content=TextBlockContent(
                    text="I'll help you create a factorial function. Here's the implementation:"
                )
            ),
            TextBlockData(
                type=ContentBlockCategory.TEXT_BLOCK,
                content=TextBlockContent(
                    text="""<thinking>
The user wants a factorial function using recursion. I need to implement proper error handling for negative numbers and edge cases.
</thinking>

<code_block>
<programming_language>python</programming_language>
<file_path>src/math_utils.py</file_path>
<is_diff>false</is_diff>
def factorial(n):
    \"\"\"\"
    Calculate factorial of a number using recursion.
    
    Args:
        n (int): Non-negative integer
        
    Returns:
        int: Factorial of n
        
    Raises:
        ValueError: If n is negative
        TypeError: If n is not an integer
    \"\"\"\"
    if not isinstance(n, int):
        raise TypeError("Input must be an integer")
    
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    
    if n <= 1:
        return 1
    
    return n * factorial(n - 1)
</code_block>

<summary>
I've implemented a recursive factorial function with proper error handling. The function includes:
1. Type checking to ensure input is an integer
2. Validation for negative numbers
3. Base case handling for 0 and 1
4. Recursive calculation for other values
5. Comprehensive docstring with examples
</summary>"""
                )
            )
        ]

    @staticmethod
    def get_code_block_examples() -> List[str]:
        """Get various code block examples for testing."""
        return [
            # Python code block
            """<code_block>
<programming_language>python</programming_language>
<file_path>src/calculator.py</file_path>
<is_diff>false</is_diff>
class Calculator:
    def add(self, a, b):
        return a + b
</code_block>""",
            
            # JavaScript code block with diff
            """<code_block>
<programming_language>javascript</programming_language>
<file_path>src/components/Button.jsx</file_path>
<is_diff>true</is_diff>
@@ -1,5 +1,7 @@
 import React from 'react';
 
-function Button({ children }) {
+function Button({ children, onClick, disabled = false }) {
   return (
-    <button>{children}</button>
+    <button onClick={onClick} disabled={disabled}>
+      {children}
+    </button>
   );
 }
</code_block>""",
            
            # TypeScript code block
            """<code_block>
<programming_language>typescript</programming_language>
<file_path>src/types/user.ts</file_path>
<is_diff>false</is_diff>
interface User {
  id: number;
  name: string;
  email: string;
  createdAt: Date;
}

export default User;
</code_block>""",
            
            # SQL code block  
            """<code_block>
<programming_language>sql</programming_language>
<file_path>migrations/001_create_users.sql</file_path>
<is_diff>false</is_diff>
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
</code_block>"""
        ]

    @staticmethod
    def get_thinking_examples() -> List[str]:
        """Get thinking block examples for testing."""
        return [
            """<thinking>
The user is asking for a factorial function. I need to consider:
1. Recursive implementation as requested
2. Error handling for edge cases
3. Proper documentation
4. Performance considerations for large numbers
</thinking>""",
            
            """<thinking>
For this REST API implementation, I should:
1. Set up proper project structure
2. Implement authentication middleware
3. Create database models with relationships
4. Add comprehensive error handling
5. Include unit tests with good coverage
6. Follow REST conventions for endpoints
</thinking>""",
            
            """<thinking>
The diff shows we're adding onClick and disabled props to the Button component.
This is a common pattern in React for making components more reusable.
I should ensure proper TypeScript types if this were a .tsx file.
</thinking>"""
        ]

    @staticmethod
    def get_summary_examples() -> List[str]:
        """Get summary block examples for testing."""
        return [
            """<summary>
I've implemented a recursive factorial function with comprehensive error handling:
- Type validation for integer inputs
- Error handling for negative numbers  
- Proper base case for 0 and 1
- Clear documentation with examples
- Follows Python best practices
</summary>""",
            
            """<summary>
I've created a complete REST API structure with:
- User authentication using JWT tokens
- Database models with SQLAlchemy ORM
- RESTful endpoint design
- Comprehensive unit test coverage
- Proper error handling and validation
- Configuration management for different environments
</summary>""",
            
            """<summary>
Updated the Button component to be more flexible:
- Added onClick handler prop
- Added disabled state with default value
- Maintained backward compatibility
- Component is now more reusable across the application
</summary>"""
        ]

    @staticmethod
    def get_malformed_examples() -> List[str]:
        """Get malformed input examples for error handling tests."""
        return [
            "",  # Empty string
            "<thinking>Incomplete thinking block",  # Unclosed tag
            "<code_block>No metadata tags</code_block>",  # Missing required metadata
            "Just plain text with no XML",  # No XML structure
            "<invalid_tag>Some content</invalid_tag>",  # Invalid tag
            "<thinking></thinking>",  # Empty thinking
            """<code_block>
<programming_language></programming_language>
<file_path></file_path>
<is_diff>invalid</is_diff>
</code_block>""",  # Invalid metadata values
        ]

    @staticmethod
    def get_mixed_content_examples() -> List[str]:
        """Get examples with mixed content types for comprehensive testing."""
        return [
            """<thinking>
I need to implement both a utility function and update the main application.
</thinking>

<code_block>
<programming_language>python</programming_language>
<file_path>src/utils.py</file_path>
<is_diff>false</is_diff>
def validate_email(email):
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
</code_block>

<code_block>
<programming_language>python</programming_language>
<file_path>src/main.py</file_path>
<is_diff>true</is_diff>
@@ -1,3 +1,5 @@
+from src.utils import validate_email
+
 def main():
-    print("Hello World")
+    email = input("Enter email: ")
+    if validate_email(email):
+        print("Valid email!")
+    else:
+        print("Invalid email format")
</code_block>

<summary>
I've added an email validation utility function and updated the main application to use it:
1. Created validate_email function using regex pattern
2. Updated main.py to import and use the validation
3. Added user input handling with validation feedback
</summary>""",
            
            """Some introductory text before the blocks.

<thinking>
Multiple code blocks with different languages coming up.
</thinking>

<code_block>
<programming_language>html</programming_language>
<file_path>templates/index.html</file_path>
<is_diff>false</is_diff>
<!DOCTYPE html>
<html>
<head>
    <title>My App</title>
</head>
<body>
    <h1>Welcome</h1>
</body>
</html>
</code_block>

<code_block>
<programming_language>css</programming_language>
<file_path>static/styles.css</file_path>
<is_diff>false</is_diff>
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f5f5f5;
}

h1 {
    color: #333;
    text-align: center;
}
</code_block>

Additional explanatory text between blocks.

<summary>
Created basic HTML template with accompanying CSS styles for a clean, centered layout.
</summary>"""
        ]