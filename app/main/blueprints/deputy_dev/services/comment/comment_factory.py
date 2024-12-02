from app.main.blueprints.deputy_dev.constants.repo import VCSTypes
from app.main.blueprints.deputy_dev.services.comment.base_comment import BaseComment
from app.main.blueprints.deputy_dev.services.comment.bitbucket_comment import (
    BitbucketComment,
)
from app.main.blueprints.deputy_dev.services.comment.github_comment import GithubComment
from app.main.blueprints.deputy_dev.services.comment.gitlab_comment import GitlabComment
from app.main.blueprints.deputy_dev.services.credentials import AuthHandler


class CommentFactory:
    FACTORIES = {
        VCSTypes.bitbucket.value: BitbucketComment,
        VCSTypes.github.value: GithubComment,
        VCSTypes.gitlab.value: GitlabComment,
    }

    @classmethod
    async def initialize(
        cls,
        vcs_type: str,
        workspace,
        workspace_slug,
        repo_name,
        pr_id,
        auth_handler: AuthHandler,
        pr_details=None,
        repo_id=None,
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
