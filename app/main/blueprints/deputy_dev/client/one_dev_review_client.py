from typing import Any, Dict

from deputydev_core.clients.http.base_http_client import BaseHTTPClient
from deputydev_core.utils.config_manager import ConfigManager
from deputydev_core.utils.constants.enums import Clients


class OneDevReviewClient(BaseHTTPClient):
    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        timeout = ConfigManager.configs["ONE_DEV"].get("TIMEOUT") or 60
        # The total number of simultaneous connections allowed (default is 100). (set 0 for unlimited)
        limit = ConfigManager.configs["ONE_DEV"].get("LIMIT") or 0
        # The maximum number of connections allowed per host (default is 0, meaning unlimited).
        limit_per_host = ConfigManager.configs["ONE_DEV"].get("LIMIT_PER_HOST") or 0
        # ttl_dns_cache: Time-to-live (TTL) for DNS cache entries, in seconds (default is 10).
        ttl_dns_cache = ConfigManager.configs["ONE_DEV"].get("TTL_DNS_CACHE") or 10
        super().__init__(
            timeout=timeout,
            limit=limit,
            limit_per_host=limit_per_host,
            ttl_dns_cache=ttl_dns_cache,
        )

    def get_reranking_base_url(self) -> str:
        return ConfigManager.configs["ONE_DEV"]["HOST"]

    def get_embedding_base_url(self) -> str:
        return ConfigManager.configs["EMBEDDING_SERVICE_HOST"]

    async def create_embedding(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        path = f"{self.get_embedding_base_url()}/end_user/v1/code-gen/create-embedding"
        result = await self.post(
            url=path,
            json=payload,
            headers={**headers, "X-Client-Version": "2.0.1", "X-Client": Clients.PR_REVIEW.value},
        )
        return (await result.json()).get("data")

    async def llm_reranking(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        path = f"{self.get_reranking_base_url()}/end_user/v1/chunks/rerank-via-llm"
        headers = {**headers, "X-Client-Version": "2.0.1", "X-Client": Clients.PR_REVIEW.value}
        result = await self.post(url=path, json=payload, headers=headers)
        return (await result.json()).get("data")
