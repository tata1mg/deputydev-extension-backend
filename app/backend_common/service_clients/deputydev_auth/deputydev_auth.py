from typing import Any, Dict, Optional

import aiohttp
from deputydev_core.utils.config_manager import ConfigManager

from app.backend_common.service_clients.deputydev_auth.endpoints import AuthEndpoint


class DeputyDevAuthClient:
    def __init__(
        self,
        timeout: int = ConfigManager.configs["DEPUTY_DEV_AUTH"]["TIMEOUT"],
    ) -> None:
        """
        Simple aiohttp-based HTTP client for DeputyDev Auth service.
        Each request uses its own aiohttp.ClientSession unless you
        explicitly manage one externally.
        """
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.connector = aiohttp.TCPConnector()

    def get_auth_base_url(self) -> str:
        return ConfigManager.configs["DEPUTY_DEV_AUTH"]["HOST"]

    async def _request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        async with aiohttp.ClientSession(connector=self.connector, timeout=self.timeout) as session:
            async with session.request(method=method, url=url, headers=headers, params=params, json=json) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def get_auth_data(self, headers: Dict[str, str], params: Dict[str, str]) -> Dict[str, Any]:
        path = f"{self.get_auth_base_url()}{AuthEndpoint.GET_AUTH_DATA.value}"
        result = await self._request("GET", path, headers=headers, params=params)
        return result

    async def get_session(self, headers: Dict[str, str]) -> Dict[str, Any]:
        path = f"{self.get_auth_base_url()}{AuthEndpoint.GET_SESSION.value}"
        result = await self._request("GET", path, headers=headers)
        return result

    async def verify_auth_token(self, headers: Dict[str, str]) -> Dict[str, Any]:
        path = f"{self.get_auth_base_url()}{AuthEndpoint.VERIFY_AUTH_TOKEN.value}"
        result = await self._request("POST", path, headers=headers)
        return result

    async def sign_up(self, headers: Dict[str, str]) -> Dict[str, Any]:
        path = f"{self.get_auth_base_url()}{AuthEndpoint.SIGN_UP.value}"
        result = await self._request("POST", path, headers=headers)
        return result
