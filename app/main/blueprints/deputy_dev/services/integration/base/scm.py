from __future__ import annotations

from abc import ABC, abstractmethod

from torpedo import CONFIG

from app.main.blueprints.deputy_dev.services.jwt_service import JWTService

from ...credentials import AuthHandler


class SCM(ABC):
    WEBHOOKS_PAYLOAD = CONFIG.config.get("WEBHOOKS_PAYLOAD")

    def __init__(self, auth_handler: AuthHandler | None = None):
        pass

    @abstractmethod
    async def create_webhooks(self, *args, **kwargs):
        pass

    @abstractmethod
    async def list_all_workspaces(self, *args, **kwargs):
        pass

    @staticmethod
    def _prepare_url(base_url, vcs_type, scm_workspace_id):
        payload = {
            "vcs_type": vcs_type,
            "prompt_version": "v2",
            "scm_workspace_id": scm_workspace_id,
        }
        token = JWTService.encode(payload=payload)

        return f"{base_url}?data={token}"

    # @abstractmethod
    # def list_all_repos(self):
    #     pass

    # @abstractmethod
    # def list_all_users(self):
    #     pass
