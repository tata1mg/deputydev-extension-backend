from __future__ import annotations

from abc import ABC, abstractmethod

from torpedo import CONFIG

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
    def _prepare_url(base_url, vcs_type):
        return f"{base_url}&vcs_type={vcs_type}&prompt_version=v2"

    # @abstractmethod
    # def list_all_repos(self):
    #     pass

    # @abstractmethod
    # def list_all_users(self):
    #     pass
