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
        diff --git a/app/managers/sku_offer/sku_offer_manager.py b/app/managers/sku_offer/sku_offer_manager.py
        index 3c03ff2e..df5fa3d1 100644
        --- a/app/managers/sku_offer/sku_offer_manager.py
        +++ b/app/managers/sku_offer/sku_offer_manager.py
        @@ -4,7 +4,6 @@ import json
         from sanic.log import logger
         
         from app.constants.enum import DiscountingPhaseTwoExperiment
        -from app.service_clients.order.order import OrdersClient
         from app.service_clients.search.search import SearchClient
         from app.service_clients.subscription.subscription import SubscriptionServiceClient
        """
        cache_key = f"code_diff:{self.review_id}"
        pr_diff = await ExtensionReviewCache.get(cache_key)
        if pr_diff is None:
            raise ValueError(f"PR diff not found in cache for review_id={self.review_id}")

        if append_line_no_info:
            return append_line_numbers(pr_diff)
        return pr_diff
