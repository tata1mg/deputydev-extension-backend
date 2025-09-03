from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from deputydev_core.utils.jwt_handler import JWTHandler

from app.backend_common.utils.sanic_wrapper import CONFIG

from .......backend_common.services.credentials import AuthHandler


class SCM(ABC):
    WEBHOOKS_PAYLOAD = CONFIG.config.get("WEBHOOKS_PAYLOAD")

    def __init__(self, auth_handler: AuthHandler | None = None) -> None:
        pass

    @abstractmethod
    async def create_webhooks(self, *args: Any, **kwargs: Any) -> None:
        pass

    @abstractmethod
    async def list_all_workspaces(self, *args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
        pass

    @staticmethod
    def _prepare_url(base_url: str, vcs_type: str, scm_workspace_id: str) -> str:
        payload = {
            "vcs_type": vcs_type,
            "prompt_version": "v2",
            "scm_workspace_id": scm_workspace_id,
        }
        token = JWTHandler(signing_key=CONFIG.config["WEBHOOK_JWT_SIGNING_KEY"]).create_token(payload=payload)

        return f"{base_url}?data={token}"
