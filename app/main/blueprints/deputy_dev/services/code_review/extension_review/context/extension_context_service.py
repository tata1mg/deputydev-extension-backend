from app.backend_common.caches.extension_review_cache import ExtensionReviewCache
from app.backend_common.utils.formatting import append_line_numbers


class ExtensionContextService:
    def __init__(self, review_id: int):
        self.review_id = review_id

    async def get_pr_diff(self, append_line_no_info: bool = False) -> str:
        """
        Fetch the PR diff from cache using a composite key of review_id and repo_id.
        Optionally append line numbers to the diff.

        Args:
            append_line_no_info (bool): Whether to append line numbers to the diff.

        Returns:
            str: The PR diff, optionally with line numbers.
        """
        return """
        diff --git a/torpedo/utils/math_utils.py b/torpedo/utils/math_utils.py
        new file mode 100644
        index 00000000..b7e23a1f
        --- /dev/null
        +++ b/torpedo/utils/math_utils.py
        @@ -0,0 +1,12 @@
        +def add(a, b):
        +    # Adds two numbers
        +    return a + b
        +
        +
        +def divide(a, b):
        +    return a / 0
        +
        +
        +def multiply(a, b):
        +    # Multiplies two numbers
        +    return a * b
        """
        cache_key = f"code_diff:{self.review_id}"
        pr_diff = await ExtensionReviewCache.get(cache_key)
        if pr_diff is None:
            raise ValueError(f"PR diff not found in cache for review_id={self.review_id}")

        if append_line_no_info:
            return append_line_numbers(pr_diff)
        return pr_diff
