from __future__ import annotations

from .base import SCM, Integration
from .bitbucket import Bitbucket
from .confluence import Confluence
from .factory import get_integration
from .github import Github
from .gitlab import Gitlab
from .jira import Jira

__all__ = [
    "SCM",
    "Integration",
    "Bitbucket",
    "Confluence",
    "Github",
    "Gitlab",
    "Jira",
    "get_integration",
]
