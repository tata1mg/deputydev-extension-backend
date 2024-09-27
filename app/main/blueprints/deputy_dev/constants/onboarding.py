from enum import Enum


class UserRoles(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"
    INSTALLATION = "installation"  # github instalation id
    WORKSPACE_ACCESS = "workspace_access"


class TokenableType(str, Enum):
    TEAM = "team"
    INTEGRATION = "integration"
    WORKSPACE = "workspace"


class IntegrationClient(str, Enum):
    # -- scm --
    BITBUCKET = "bitbucket"
    GITLAB = "gitlab"
    GITHUB = "github"
    # -- issue tracker --
    JIRA = "jira"
    # -- knowledge base --
    CONFLUENCE = "confluence"
