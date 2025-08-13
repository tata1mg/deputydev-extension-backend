from typing import Dict, Optional, Type

from app.backend_common.constants.constants import VCSTypes
from app.backend_common.services.credentials import AuthHandler
from app.backend_common.services.pr.dataclasses.main import PullRequestResponse
from app.main.blueprints.deputy_dev.services.comment.base_comment import BaseComment
from app.main.blueprints.deputy_dev.services.comment.bitbucket_comment import (
    BitbucketComment,
)
from app.main.blueprints.deputy_dev.services.comment.github_comment import GithubComment
from app.main.blueprints.deputy_dev.services.comment.gitlab_comment import GitlabComment


class CommentFactory:
    FACTORIES: Dict[str, Type[BaseComment]] = {
        VCSTypes.bitbucket.value: BitbucketComment,
        VCSTypes.github.value: GithubComment,
        VCSTypes.gitlab.value: GitlabComment,
    }

    @classmethod
    async def initialize(
        cls,
        vcs_type: str,
        workspace: str,
        workspace_slug: str,
        repo_name: str,
        pr_id: str,
        auth_handler: AuthHandler,
        pr_details: Optional[PullRequestResponse] = None,
        repo_id: Optional[int] = None,
    ) -> BaseComment:
        if vcs_type not in cls.FACTORIES:
            raise ValueError("Incorrect vcs type passed")
        _klass = cls.FACTORIES[vcs_type]
        _klass_obj = _klass(
            workspace=workspace,
            workspace_slug=workspace_slug,
            pr_id=pr_id,
            repo_name=repo_name,
            pr_details=pr_details,
            auth_handler=auth_handler,
            repo_id=repo_id,
        )
        return _klass_obj
