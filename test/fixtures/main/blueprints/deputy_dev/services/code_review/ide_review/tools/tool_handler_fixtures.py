from typing import Any, Dict, List


class ExtensionToolHandlersFixtures:
    """Fixtures for ExtensionToolHandlers tests."""

    @staticmethod
    def get_parse_final_response_input_with_data() -> Dict[str, Any]:
        """Return tool input with comments and summary."""
        return {
            "comments": [
                {"line": 1, "message": "Consider using a more descriptive variable name", "severity": "medium"},
                {"line": 5, "message": "This function could be optimized", "severity": "low"},
            ],
            "summary": "Overall code quality is good with minor improvements needed",
        }

    @staticmethod
    def get_empty_tool_input() -> Dict[str, Any]:
        """Return empty tool input."""
        return {}

    @staticmethod
    def get_tool_input_missing_keys() -> Dict[str, Any]:
        """Return tool input with missing required keys."""
        return {"other_key": "other_value"}

    @staticmethod
    def get_parse_final_response_with_complex_data() -> Dict[str, Any]:
        """Return tool input with complex data types."""
        return {
            "comments": [
                {
                    "id": 1,
                    "line": 10,
                    "message": "Complex comment with nested data",
                    "metadata": {
                        "author": "test_user",
                        "timestamp": "2023-01-01T00:00:00Z",
                        "tags": ["security", "performance"],
                    },
                }
            ],
            "summary": "Detailed summary with multiple sentences. This includes various aspects of the code review.",
        }

    @staticmethod
    def get_pr_review_planner_input() -> Dict[str, Any]:
        """Return tool input for pr_review_planner."""
        return {
            "review_focus": "security and performance",
            "additional_context": "Focus on authentication and database queries",
        }

    @staticmethod
    def get_tool_input_without_review_focus() -> Dict[str, Any]:
        """Return tool input without review_focus key."""
        return {"additional_context": "Some other context"}

    @staticmethod
    def get_sample_pr_diff() -> str:
        """Return a sample PR diff."""
        return """diff --git a/example.py b/example.py
index 1234567..abcdefg 100644
--- a/example.py
+++ b/example.py
@@ -1,5 +1,7 @@
 def hello_world():
-    print("Hello, World!")
+    print("Hello, World!")
+    print("This is a new line")
     
 def goodbye():
-    print("Goodbye!")
+    print("Goodbye!")
+    return True"""

    @staticmethod
    def get_sample_review_plan() -> Dict[str, Any]:
        """Return a sample review plan."""
        return {
            "review_plan": {
                "focus_areas": ["security", "performance"],
                "files_to_review": ["example.py", "config.py"],
                "estimated_time": "30 minutes",
                "priority": "high",
            },
            "suggestions": [
                "Review authentication logic",
                "Check for SQL injection vulnerabilities",
                "Analyze performance bottlenecks",
            ],
        }

    @staticmethod
    def get_various_session_ids() -> List[int]:
        """Return various session IDs for testing."""
        return [1, 123, 456, 789, 999, 0, -1, 9999999]

    @staticmethod
    def get_prompt_vars_template() -> Dict[str, str]:
        """Return template for prompt variables."""
        return {"PULL_REQUEST_TITLE": "NA", "PULL_REQUEST_DESCRIPTION": "NA", "PULL_REQUEST_DIFF": "", "FOCUS_AREA": ""}

    @staticmethod
    def get_comments_with_various_types() -> List[Dict[str, Any]]:
        """Return comments with various data types."""
        return [
            {
                "line": 1,
                "message": "String comment",
                "severity": "high",
                "is_blocking": True,
                "score": 8.5,
                "tags": ["bug", "critical"],
                "metadata": None,
            },
            {
                "line": 15,
                "message": "Another comment",
                "severity": "low",
                "is_blocking": False,
                "score": 3.2,
                "tags": [],
                "metadata": {"category": "style", "auto_fixable": True},
            },
        ]

    @staticmethod
    def get_summaries_with_various_content() -> List[str]:
        """Return summaries with various content."""
        return [
            "",
            "Short summary",
            "This is a longer summary with multiple sentences. It contains detailed information about the code review.",
            "Summary with special characters: @#$%^&*()_+{}|:<>?[]\\;'\",./",
        ]
