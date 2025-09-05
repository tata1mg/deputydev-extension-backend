from typing import Any, Dict

from deputydev_core.clients.http.base_http_client import BaseHTTPClient
from deputydev_core.utils.config_manager import ConfigManager

from app.backend_common.service_clients.deputydev_auth.endpoints import AuthEndpoint


class DeputyDevAuthClient(BaseHTTPClient):
    def __init__(self) -> None:
        timeout = ConfigManager.configs["DEPUTY_DEV_AUTH"]["TIMEOUT"]
        # The total number of simultaneous connections allowed (default is 100). (set 0 for unlimited)
        limit = 0
        # The maximum number of connections allowed per host (default is 0, meaning unlimited).
        limit_per_host = 0
        # ttl_dns_cache: Time-to-live (TTL) for DNS cache entries, in seconds (default is 10).
        ttl_dns_cache = 10
        super().__init__(
            timeout=timeout,
            limit=limit,
            limit_per_host=limit_per_host,
            ttl_dns_cache=ttl_dns_cache,
        )

    def get_auth_base_url(self) -> str:
        return ConfigManager.configs["DEPUTY_DEV_AUTH"]["HOST"]

    async def get_auth_data(self, headers: Dict[str, str], params: Dict[str, str]) -> Dict[str, Any]:
        path = f"{self.get_auth_base_url()}{AuthEndpoint.GET_AUTH_DATA.value}"
        result = await self.get(url=path, headers=headers, params=params)
        return await result.json()

    async def get_session(self, headers: Dict[str, str]) -> Dict[str, Any]:
        unique_session_id = headers.get("X-Unique-Session-ID", "")
        path = f"{self.get_auth_base_url()}{AuthEndpoint.GET_SESSION.value}"
        result = await self.get(url=path, headers={"X-Unique-Session-ID": unique_session_id})
        return await result.json()

    async def verify_auth_token(self, headers: Dict[str, str]) -> Dict[str, Any]:
        path = f"{self.get_auth_base_url()}{AuthEndpoint.VERIFY_AUTH_TOKEN.value}"
        result = await self.post(url=path, headers=headers)
        return await result.json()

    async def sign_up(self, headers: Dict[str, str]) -> Dict[str, Any]:
        path = f"{self.get_auth_base_url()}{AuthEndpoint.SIGN_UP.value}"
        result = await self.post(url=path, headers=headers)
        return await result.json()
