from typing import Any, Dict, List


class Gpt4Point1ParserFixtures:
    """Fixture data for GPT 4 Point 1 parser tests."""

    @staticmethod
    def get_non_diff_code_block() -> Dict[str, Any]:
        """Get a non-diff code block for testing."""
        return {
            "language": "python",
            "file_path": "main.py",
            "is_diff": False,
            "code": """def calculate_factorial(n):
    \"\"\"
    Calculate factorial of a number using recursion.
    
    Args:
        n (int): Non-negative integer
        
    Returns:
        int: Factorial of n
        
    Raises:
        ValueError: If n is negative
        TypeError: If n is not an integer
    \"\"\"
    if not isinstance(n, int):
        raise TypeError("Input must be an integer")
    
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    
    if n <= 1:
        return 1
    
    return n * calculate_factorial(n - 1)


def main():
    \"\"\"Main function to test factorial calculation.\"\"\"
    test_values = [0, 1, 5, 10]
    
    for value in test_values:
        try:
            result = calculate_factorial(value)
            print(f"Factorial of {value} is {result}")
        except (ValueError, TypeError) as e:
            print(f"Error calculating factorial of {value}: {e}")


if __name__ == "__main__":
    main()""",
        }

    @staticmethod
    def get_diff_code_block() -> Dict[str, Any]:
        """Get a diff code block for testing."""
        return {
            "language": "javascript",
            "file_path": "src/components/UserProfile.jsx",
            "is_diff": True,
            "code": """@@ -1,15 +1,25 @@
 import React from 'react';
+import PropTypes from 'prop-types';
 
-function UserProfile({ user }) {
+function UserProfile({ user, onEdit, showEditButton = true }) {
+    const handleEdit = () => {
+        if (onEdit) {
+            onEdit(user.id);
+        }
+    };
+
     return (
         <div className="user-profile">
             <img src={user.avatar} alt={user.name} />
             <h2>{user.name}</h2>
             <p>{user.email}</p>
-            <p>Member since: {user.joinDate}</p>
+            <p>Member since: {new Date(user.joinDate).toLocaleDateString()}</p>
+            {showEditButton && (
+                <button onClick={handleEdit} className="edit-btn">
+                    Edit Profile
+                </button>
+            )}
         </div>
     );
 }
 
+UserProfile.propTypes = {
+    user: PropTypes.shape({
+        id: PropTypes.number.isRequired,
+        name: PropTypes.string.isRequired,
+        email: PropTypes.string.isRequired,
+        avatar: PropTypes.string.isRequired,
+        joinDate: PropTypes.string.isRequired,
+    }).isRequired,
+    onEdit: PropTypes.func,
+    showEditButton: PropTypes.bool,
+};
+
 export default UserProfile;""",
        }

    @staticmethod
    def get_complex_diff_code_block() -> Dict[str, Any]:
        """Get a complex diff code block with multiple hunks."""
        return {
            "language": "python",
            "file_path": "src/services/auth_service.py",
            "is_diff": True,
            "code": """@@ -1,8 +1,15 @@
+import logging
+from datetime import datetime, timedelta
+from typing import Optional, Dict, Any
+
 import jwt
 from werkzeug.security import generate_password_hash, check_password_hash
 
 class AuthService:
-    def __init__(self, secret_key):
+    def __init__(self, secret_key: str, token_expiry_hours: int = 24):
         self.secret_key = secret_key
+        self.token_expiry_hours = token_expiry_hours
+        self.logger = logging.getLogger(__name__)
     
     def hash_password(self, password):
         return generate_password_hash(password)
@@ -12,15 +19,35 @@
     def verify_password(self, password, password_hash):
         return check_password_hash(password_hash, password)
     
-    def generate_token(self, user_id):
+    def generate_token(self, user_id: int, additional_claims: Optional[Dict[str, Any]] = None) -> str:
+        \"\"\"Generate JWT token for user authentication.\"\"\"
+        now = datetime.utcnow()
+        expiry = now + timedelta(hours=self.token_expiry_hours)
+        
         payload = {
             'user_id': user_id,
-            'exp': datetime.utcnow() + timedelta(hours=24)
+            'iat': now,
+            'exp': expiry,
+            'type': 'access_token'
         }
+        
+        if additional_claims:
+            payload.update(additional_claims)
+        
+        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
+        self.logger.info(f"Generated token for user {user_id}")
+        return token
+    
+    def generate_refresh_token(self, user_id: int) -> str:
+        \"\"\"Generate refresh token with longer expiry.\"\"\"
+        now = datetime.utcnow()
+        expiry = now + timedelta(days=30)
+        
+        payload = {
+            'user_id': user_id,
+            'iat': now,
+            'exp': expiry,
+            'type': 'refresh_token'
+        }
+        
         return jwt.encode(payload, self.secret_key, algorithm='HS256')
     
-    def verify_token(self, token):
+    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
+        \"\"\"Verify JWT token and return payload if valid.\"\"\"
         try:
-            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
-            return payload
-        except jwt.ExpiredSignatureError:
-            return None
-        except jwt.InvalidTokenError:
+            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
+            
+            # Verify token type
+            if payload.get('type') != 'access_token':
+                self.logger.warning(f"Invalid token type: {payload.get('type')}")
+                return None
+                
+            return payload
+        except jwt.ExpiredSignatureError:
+            self.logger.warning("Token has expired")
+            return None
+        except jwt.InvalidTokenError as e:
+            self.logger.error(f"Invalid token: {e}")
             return None""",
        }

    @staticmethod
    def get_thinking_block_examples() -> List[str]:
        """Get thinking block examples for testing."""
        return [
            """The user is asking for a factorial function with proper error handling. I need to consider:

1. Input validation - ensure the input is an integer
2. Range validation - factorial is only defined for non-negative integers
3. Base cases - factorial of 0 and 1 is 1
4. Recursive implementation as requested
5. Comprehensive error handling with meaningful messages
6. Documentation with proper docstrings

I'll implement this with proper type hints and include a main function for testing.""",
            """This React component update requires several improvements:

1. Add PropTypes for better type checking
2. Make the component more flexible with optional edit functionality
3. Improve date formatting for better user experience
4. Add proper event handling for the edit button
5. Maintain backward compatibility

The diff shows we're adding:
- PropTypes import and validation
- Optional onEdit callback prop
- showEditButton prop with default value
- Proper date formatting
- Event handler for edit functionality""",
            """For this authentication service refactor, I need to address:

1. **Type Safety**: Add proper type hints for all methods
2. **Security**: Implement refresh tokens for better security
3. **Logging**: Add comprehensive logging for debugging and security audit
4. **Token Management**: 
   - Separate access and refresh tokens
   - Configurable expiry times
   - Better payload structure
5. **Error Handling**: More granular error handling with specific error types
6. **Additional Claims**: Support for custom claims in tokens

The implementation follows JWT best practices and improves the overall security posture.""",
        ]

    @staticmethod
    def get_summary_block_examples() -> List[str]:
        """Get summary block examples for testing."""
        return [
            """I've implemented a robust factorial function with comprehensive error handling:

**Key Features:**
- Input validation for integer types
- Range validation for non-negative numbers
- Recursive implementation as requested
- Proper exception handling with meaningful error messages
- Comprehensive docstring with examples
- Test function to demonstrate usage

**Error Handling:**
- TypeError for non-integer inputs
- ValueError for negative numbers
- Graceful handling in the main function

The implementation follows Python best practices and provides clear feedback for invalid inputs.""",
            """I've enhanced the UserProfile React component with the following improvements:

**New Features:**
- PropTypes validation for better type safety
- Optional edit functionality with onEdit callback
- Configurable edit button visibility
- Improved date formatting using toLocaleDateString()
- Proper event handling for user interactions

**Backward Compatibility:**
- All new props are optional with sensible defaults
- Existing functionality remains unchanged
- Component maintains the same basic structure

**Code Quality:**
- Added comprehensive PropTypes validation
- Improved user experience with better date display
- Clean, maintainable code structure""",
            """I've significantly improved the authentication service with enhanced security and functionality:

**Security Enhancements:**
- Separate access and refresh tokens
- Configurable token expiry times
- Token type validation
- Comprehensive logging for security auditing

**Code Quality:**
- Full type hints for better IDE support and runtime safety
- Improved error handling with specific exception types
- Better structured payload with issued-at timestamps
- Support for additional custom claims

**Features Added:**
- Refresh token generation with 30-day expiry
- Enhanced token verification with type checking
- Detailed logging for authentication events
- More flexible token generation with custom claims

This implementation follows JWT security best practices and provides a robust foundation for authentication systems.""",
        ]

    @staticmethod
    def get_code_block_examples() -> List[Dict[str, Any]]:
        """Get various code block examples for testing."""
        return [
            # Python class example
            {
                "language": "python",
                "file_path": "src/models/user.py",
                "is_diff": False,
                "code": """from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class User:
    id: int
    username: str
    email: str
    created_at: datetime
    is_active: bool = True
    last_login: Optional[datetime] = None
    
    def activate(self) -> None:
        \"\"\"Activate the user account.\"\"\"
        self.is_active = True
    
    def deactivate(self) -> None:
        \"\"\"Deactivate the user account.\"\"\"
        self.is_active = False
        
    def update_last_login(self) -> None:
        \"\"\"Update the last login timestamp.\"\"\"
        self.last_login = datetime.now()
    
    def __str__(self) -> str:
        return f"User(id={self.id}, username='{self.username}', active={self.is_active})\"""",
            },
            # TypeScript interface
            {
                "language": "typescript",
                "file_path": "src/types/api.ts",
                "is_diff": False,
                "code": """export interface ApiResponse<T> {
  data: T;
  status: number;
  message: string;
  timestamp: string;
  requestId: string;
}

export interface ErrorResponse extends ApiResponse<null> {
  error: string;
  details?: Record<string, any>;
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    page: number;
    limit: number;
    total: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
}

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export interface RequestConfig {
  method: HttpMethod;
  url: string;
  headers?: Record<string, string>;
  params?: Record<string, any>;
  data?: any;
  timeout?: number;
}""",
            },
            # SQL schema
            {
                "language": "sql",
                "file_path": "migrations/003_create_orders_table.sql",
                "is_diff": False,
                "code": """-- Create orders table with proper constraints and indexes
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    total_amount DECIMAL(10, 2) NOT NULL CHECK (total_amount >= 0),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending', 'processing', 'completed', 'cancelled')),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    shipping_address TEXT NOT NULL,
    billing_address TEXT NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_order_date ON orders(order_date);
CREATE INDEX idx_orders_created_at ON orders(created_at);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_orders_updated_at 
    BEFORE UPDATE ON orders 
    FOR EACH ROW 
    EXECUTE PROCEDURE update_updated_at_column();""",
            },
        ]

    @staticmethod
    def get_malformed_examples() -> List[Dict[str, Any]]:
        """Get malformed examples for error handling tests."""
        return [
            # Missing required fields
            {
                "language": "python",
                # Missing file_path
                "is_diff": False,
                "code": "print('missing file path')",
            },
            # Invalid data types
            {
                "language": 123,  # Should be string
                "file_path": "test.py",
                "is_diff": "maybe",  # Should be boolean
                "code": "print('invalid types')",
            },
            # Empty required fields
            {"language": "", "file_path": "", "is_diff": False, "code": ""},
            # None values
            {"language": None, "file_path": None, "is_diff": None, "code": None},
        ]

    @staticmethod
    def get_text_content_examples() -> List[str]:
        """Get text content examples for TextBlockParser testing."""
        return [
            "Simple text content for testing",
            """Multi-line text content
with line breaks and
various formatting elements.""",
            """Text with special characters: áéíóú, ñ, ü, ç
And symbols: @#$%^&*()_+-=[]{}|;':\",./<>?
Unicode: 🚀 💡 ⚡ 🔥 ✨""",
            """Code-like text that's not in a code block:
def function():
    return "This is just text, not code"
    
if condition:
    do_something()""",
            """JSON-like text content:
{
    "name": "Test User",
    "email": "test@example.com",
    "settings": {
        "theme": "dark",
        "notifications": true
    }
}""",
            # Very long text
            "This is a very long text content that should test the parser's ability to handle large amounts of text data. "
            * 100,
            # Text with tabs and special whitespace
            "\t\tIndented text with tabs\n\r\nWindows line endings\n\nMultiple newlines",
            # Empty and whitespace-only content
            "",
            "   ",
            "\n\n\n",
            "\t\t\t",
        ]

    @staticmethod
    def get_streaming_event_examples() -> List[Dict[str, Any]]:
        """Get examples for streaming event testing."""
        return [
            {"event_type": "text_block_start", "content": None},
            {"event_type": "text_block_delta", "content": "This is streaming text content"},
            {"event_type": "text_block_end", "content": None},
            {
                "event_type": "tool_use_start",
                "content": {"tool_name": "file_searcher", "tool_input": {"query": "search term"}},
            },
            {"event_type": "tool_use_delta", "content": "Tool execution in progress..."},
            {"event_type": "tool_use_end", "content": {"result": "Tool execution completed", "status": "success"}},
        ]

    @staticmethod
    def get_performance_test_data() -> List[str]:
        """Get data for performance testing."""
        return [
            # Small content
            "Small test content",
            # Medium content
            "Medium sized content that should test parser performance with moderate amounts of data. " * 50,
            # Large content
            "Large content block for performance testing with substantial amounts of text data. " * 1000,
            # Very large content
            "Very large content block designed to stress test the parser with massive amounts of text. " * 5000,
        ]

    @staticmethod
    def get_edge_case_examples() -> List[Any]:
        """Get edge case examples for robust testing."""
        return [
            None,  # None input
            "",  # Empty string
            " ",  # Single space
            "\n",  # Single newline
            "\t",  # Single tab
            "\r\n",  # Windows line ending
            0,  # Zero
            [],  # Empty list
            {},  # Empty dict
            False,  # Boolean false
            True,  # Boolean true
        ]
