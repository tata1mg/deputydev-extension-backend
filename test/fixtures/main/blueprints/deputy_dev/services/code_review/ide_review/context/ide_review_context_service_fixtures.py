class IdeReviewContextServiceFixtures:
    """Fixtures for IdeReviewContextService tests."""

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
    def get_sample_pr_diff_with_line_numbers() -> str:
        """Return a sample PR diff with line numbers."""
        return """1: diff --git a/example.py b/example.py
2: index 1234567..abcdefg 100644
3: --- a/example.py
4: +++ b/example.py
5: @@ -1,5 +1,7 @@
6:  def hello_world():
7: -    print("Hello, World!")
8: +    print("Hello, World!")
9: +    print("This is a new line")
10:     
11:  def goodbye():
12: -    print("Goodbye!")
13: +    print("Goodbye!")
14: +    return True"""

    @staticmethod
    def get_empty_pr_diff() -> str:
        """Return an empty PR diff."""
        return ""

    @staticmethod
    def get_complex_pr_diff() -> str:
        """Return a complex PR diff with multiple files."""
        return """diff --git a/file1.py b/file1.py
index 1111111..2222222 100644
--- a/file1.py
+++ b/file1.py
@@ -1,3 +1,4 @@
 import os
+import sys
 
 def main():
@@ -5,2 +6,3 @@ def main():
     pass
+    return 0

diff --git a/file2.py b/file2.py
new file mode 100644
index 0000000..3333333
--- /dev/null
+++ b/file2.py
@@ -0,0 +1,5 @@
+def new_function():
+    '''This is a new function'''
+    result = 42
+    return result
+"""

    @staticmethod
    def get_cache_keys() -> dict[int, str]:
        """Return mapping of review IDs to cache keys."""
        return {
            123: "123",
            456: "456",
            789: "789",
            999: "999",
            111: "111",
            222: "222"
        }

    @staticmethod
    def get_review_ids() -> list[int]:
        """Return list of sample review IDs."""
        return [123, 456, 789, 999, 111, 222, 0, -1, 9999999]