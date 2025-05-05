from typing import Any, Dict, Optional

from deputydev_core.clients.http.base_http_client import BaseHTTPClient
from deputydev_core.utils.config_manager import ConfigManager



class OneDevReviewClient(BaseHTTPClient):

    def get_base_url(self):
        return ConfigManager.configs["ONE_DEV"]["HOST"]


    async def create_embedding(self, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
        path = f"{self.get_base_url()}/end_user/v1/code-gen/create-embedding"
        result = await self.post(
            url=path, json=payload, headers={**headers, "X-Client-Version": "1.5.0", "X-Client": "REVIEW"}
        )
        return (await result.json()).get("data")

    async def llm_reranking(self, payload: Dict[str, Any], headers: Dict[str, str]):
        path = f"{self.get_base_url()}/end_user/v1/chunks/rerank-via-llm"
        headers={**headers, "X-Client-Version": "1.5.0", "X-Client": "REVIEW"}
        result = await self.post(url=path, json=payload, headers=headers)
        return (await result.json()).get("data")
