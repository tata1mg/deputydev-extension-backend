from enum import Enum


class UserRoles(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"


class IntegrationClient(str, Enum):
    # -- scm --
    BITBUCKET = "bitbucket"
    GITLAB = "gitlab"
    GITHUB = "github"
    # -- issue tracker --
    JIRA = "jira"
    # -- knowledge base --
    CONFLUENCE = "confluence"
