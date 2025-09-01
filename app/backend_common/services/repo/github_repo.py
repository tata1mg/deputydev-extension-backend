import base64
from typing import Any, Dict, Optional, Tuple

import toml
from git.util import Actor

from app.backend_common.constants.constants import (
    SETTING_ERROR_MESSAGE,
    SettingErrorType,
    VCSTypes,
)
from app.backend_common.service_clients.github.github_repo_client import (
    GithubRepoClient,
)
from app.backend_common.services.credentials import AuthHandler
from app.backend_common.services.repo.base_repo import BaseRepo
from app.backend_common.utils.sanic_wrapper import CONFIG


class GithubRepo(BaseRepo):
    def __init__(
        self,
        workspace: str,
        repo_name: str,
        workspace_id: str,
        workspace_slug: str,
        auth_handler: AuthHandler,
        repo_id: str | None = None,
    ) -> None:
        super().__init__(
            vcs_type=VCSTypes.github.value,
            workspace=workspace,
            repo_name=repo_name,
            workspace_id=workspace_id,
            workspace_slug=workspace_slug,
            repo_id=repo_id,
            auth_handler=auth_handler,
        )
        self.repo_client = GithubRepoClient(
            workspace_slug=workspace_slug, repo=repo_name, pr_id=None, auth_handler=auth_handler
        )
        self.token = ""  # Assuming I will get token here

    """
    Manages Github Repo
    """

    @staticmethod
    def get_remote_host() -> str:
        return "github.com"

    async def get_repo_url(self) -> str:
        self.token = await self.auth_handler.access_token()
        return f"https://x-token-auth:{self.token}@{self.get_remote_host()}/{self.workspace_slug}/{self.repo_name}.git"

    async def get_settings(self, branch_name: str) -> Tuple[Dict[str, Any], Dict[str, str] | str]:
        settings = await self.repo_client.get_file(branch_name, CONFIG.config["REPO_SETTINGS_FILE"])
        if settings:
            try:
                decoded_settings = base64.b64decode(settings).decode("utf-8")
                settings = toml.loads(decoded_settings)
                return settings, ""
            except toml.TomlDecodeError as e:
                error_type = SettingErrorType.INVALID_TOML.value
                error = {error_type: f"""{SETTING_ERROR_MESSAGE[error_type]}{str(e)}"""}
                return {}, error
        else:
            return {}, ""

    async def is_pr_open_between_branches(
        self, source_branch: str, destination_branch: str
    ) -> Tuple[bool, Optional[str]]:
        prs = await self.repo_client.list_prs(source=source_branch, destination=destination_branch)
        if prs:
            pr = prs[0]  # get first pr
            return True, pr["html_url"]
        return False, None

    def get_remote_url_without_token(self) -> str:
        return f"git@{self.get_remote_host()}:{self.workspace_slug}/{self.repo_name}.git"

    def get_repo_actor(self) -> Actor:
        return self.auth_handler.get_git_actor()
