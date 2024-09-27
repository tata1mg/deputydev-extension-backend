from .auth_handler import AuthHandler
from .bitbucket_auth_handler import BitbucketAuthHandler
from .confluence_auth_handler import ConfluenceAuthHandler
from .github_auth_handler import GithubAuthHandler
from .gitlab_auth_handler import GitlabAuthHandler
from .jira_auth_handler import JiraAuthHandler

STRATEGY = {
    "bitbucket": BitbucketAuthHandler,
    "gitlab": GitlabAuthHandler,
    "github": GithubAuthHandler,
    "jira": JiraAuthHandler,
    "confluence": ConfluenceAuthHandler,
}


def create_auth_handler(integration: str, tokenable_id: int) -> AuthHandler:
    return STRATEGY[integration](tokenable_id=tokenable_id)
