from app.backend_common.constants.constants import VCSTypes
from app.backend_common.service_clients.gitlab.gitlab_repo_client import (
    GitlabRepoClient,
)
from app.backend_common.services.credentials import AuthHandler
from app.backend_common.services.repo.base_repo import BaseRepo


class GitlabRepo(BaseRepo):
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
            vcs_type=VCSTypes.gitlab.value,
            workspace=workspace,
            repo_name=repo_name,
            workspace_id=workspace_id,
            workspace_slug=workspace_slug,
            repo_id=repo_id,
            auth_handler=auth_handler,
        )
        self.repo_client = GitlabRepoClient(pr_id=None, project_id=self.repo_id, auth_handler=auth_handler)
        self.token = ""

    @staticmethod
    def get_remote_host() -> str:
        return "gitlab.com"

    def get_repo_url(self) -> str:
        return f"https://x-token-auth:{self.token}@{self.get_remote_host()}/{self.workspace_slug}/{self.repo_name}.git"

    def get_remote_url_without_token(self) -> str:
        return f"git@{self.get_remote_host()}:{self.workspace_slug}/{self.repo_name}.git"
