from app.backend_common.service_clients.gitlab.gitlab_repo_client import (
    GitlabRepoClient,
)
from app.backend_common.services.credentials import AuthHandler
from app.backend_common.services.repo.base_repo import BaseRepo
from app.common.constants.constants import VCSTypes


class GitlabRepo(BaseRepo):
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
            vcs_type=VCSTypes.gitlab.value,
            workspace=workspace,
            repo_name=repo_name,
            workspace_id=workspace_id,
            workspace_slug=workspace_slug,
            repo_id=repo_id,
            auth_handler=auth_handler,
        )
        self.repo_client = GitlabRepoClient(pr_id=None, project_id=self.repo_id, auth_handler=auth_handler)

    def get_repo_url(self):
        return "https://x-token-auth:{token}@gitlab.com/{workspace_slug}/{repo_name}.git".format(
            token=self.token, workspace_slug=self.workspace_slug, repo_name=self.repo_name
        )
