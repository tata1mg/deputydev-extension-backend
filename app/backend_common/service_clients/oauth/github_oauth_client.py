from __future__ import annotations

import json
import time

import jwt
from deputydev_core.clients.http.base_http_session_manager import SessionManager

from app.backend_common.utils.sanic_wrapper import CONFIG


class GithubOAuthClient:
    CLIENT_ID = CONFIG.config["GITHUB"]["CLIENT_ID"]
    SIGNING_KEY = json.loads(CONFIG.config["GITHUB"]["SIGNING_KEY"])
    SESSION_MANAGER = SessionManager()
    ALGORITHM = "RS256"
    JWT_EXP_DELTA = 600  # 10 minutes (max)

    @classmethod
    async def get_access_token(cls, installation_id: str) -> dict:
        url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"

        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {cls.generate_jwt()}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        # NOTE: Yes, it is a POST request
        session = await cls.SESSION_MANAGER.get_session()
        async with session.post(url=url, headers=headers) as response:
            response.raise_for_status()
            return await response.json()

    @classmethod
    async def get_installation(cls, installation_id: str) -> dict:
        url = f"https://api.github.com/app/installations/{installation_id}"

        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {cls.generate_jwt()}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        session = await cls.SESSION_MANAGER.get_session()
        async with session.get(url=url, headers=headers) as response:
            response.raise_for_status()
            return await response.json()

    @classmethod
    def generate_jwt(cls) -> str:
        payload = {
            "iat": int(time.time()),  # issued at time
            "exp": int(time.time()) + cls.JWT_EXP_DELTA,
            "iss": cls.CLIENT_ID,
        }
        encoded_jwt = jwt.encode(payload=payload, key=cls.SIGNING_KEY, algorithm=cls.ALGORITHM)
        return encoded_jwt
