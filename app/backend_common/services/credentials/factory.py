from app.backend_common.models.dto.workspace_dto import WorkspaceDTO

from .auth_handler import AuthHandler
from .bitbucket_auth_handler import BitbucketAuthHandler
from .confluence_auth_handler import ConfluenceAuthHandler
from .github_auth_handler import GithubAuthHandler
from .gitlab_auth_handler import GitlabAuthHandler
from .jira_auth_handler import JiraAuthHandler


class AuthHandlerFactory:
    STRATEGY = {
        "bitbucket": BitbucketAuthHandler,
        "gitlab": GitlabAuthHandler,
        "github": GithubAuthHandler,
        "jira": JiraAuthHandler,
        "confluence": ConfluenceAuthHandler,
    }

    @classmethod
    def create_auth_handler(cls, integration: str, tokenable_id: int) -> AuthHandler:
        return cls.STRATEGY[integration](tokenable_id=tokenable_id)

    @classmethod
    def create_vcs_auth_handler(cls, workspace: WorkspaceDTO) -> AuthHandler:
        return cls.create_auth_handler(
            integration=workspace.scm,
            tokenable_id=workspace.integration_id if workspace.scm != "github" else workspace.id,
        )
