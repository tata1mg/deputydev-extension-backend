from app.backend_common.caches.ide_review_cache import IdeReviewCache
from app.backend_common.utils.formatting import append_line_numbers


class IdeReviewContextService:
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
        cache_key = f"{self.review_id}"
        pr_diff = await IdeReviewCache.get(cache_key)
        if pr_diff is None:
            raise ValueError(f"PR diff not found in cache for review_id={self.review_id}")

        if append_line_no_info:
            return append_line_numbers(pr_diff)
        return pr_diff
