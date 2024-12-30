from typing import Optional

import aiohttp
from commonutils.utils import Singleton
from torpedo import CONFIG

config = CONFIG.config


class SessionManager(metaclass=Singleton):
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create shared session"""
        # # TODO move to config before release
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=config["AIOHTTP"]["LIMIT"],
                limit_per_host=config["AIOHTTP"]["LIMIT_PER_HOST"],
                ttl_dns_cache=config["AIOHTTP"]["TTL_DNS_CACHE"],
            )
            timeout = aiohttp.ClientTimeout(total=60)
            self._session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self._session

    async def close(self):
        """Close the shared session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
