from __future__ import annotations

from typing import TypeVar

from .base import SCM, Integration
from .bitbucket import Bitbucket
from .confluence import Confluence
from .github import Github
from .gitlab import Gitlab
from .jira import Jira

STRATEGY = {
    "bitbucket": Bitbucket,
    "github": Github,
    "gitlab": Gitlab,
    "jira": Jira,
    "confluence": Confluence,
}


class SCMIntegration(Integration, SCM):
    pass


def get_integration(
    integration_name: str,
) -> TypeVar[Integration] | TypeVar[SCMIntegration]:
    return STRATEGY[integration_name]
