import base64

import toml
from torpedo import CONFIG

from app.common.service_clients.github.github_repo_client import GithubRepoClient
from app.common.services.credentials import AuthHandler
from app.common.services.repo.base_repo import BaseRepo
from app.main.blueprints.deputy_dev.constants.constants import (
    SETTING_ERROR_MESSAGE,
    SettingErrorType,
)
from app.main.blueprints.deputy_dev.constants.repo import VCS_REPO_URL_MAP, VCSTypes


class GithubRepo(BaseRepo):
    def __init__(
        self,
        workspace: str,
        repo_name: str,
        workspace_id: str,
        workspace_slug: str,
        auth_handler: AuthHandler,
        repo_id: str = None,
    ):
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

    async def get_repo_url(self):
        self.token = await self.auth_handler.access_token()
        return VCS_REPO_URL_MAP[self.vcs_type].format(
            token=self.token, workspace_slug=self.workspace_slug, repo_name=self.repo_name
        )

    async def get_settings(self, branch_name):
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
