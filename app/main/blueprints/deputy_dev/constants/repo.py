from enum import Enum


class VCSTypes(str, Enum):
    bitbucket = "bitbucket"
    gitlab = "gitlab"
    github = "github"


class RepoUrl(Enum):
    BITBUCKET_URL = "https://x-token-auth:{token}@bitbucket.org/{workspace_slug}/{repo_name}.git"
    GITHUB_URL = "https://x-token-auth:{token}@github.com/{workspace_slug}/{repo_name}.git"
    GITLAB_URL = "https://x-token-auth:{token}@gitlab.com/{workspace_slug}/{repo_name}.git"


VCS_REPO_URL_MAP = {
    VCSTypes.bitbucket.value: RepoUrl.BITBUCKET_URL.value,
    VCSTypes.github.value: RepoUrl.GITHUB_URL.value,
    VCSTypes.gitlab.value: RepoUrl.GITLAB_URL.value,
}

PR_NOT_FOUND = "PR does not exist"
