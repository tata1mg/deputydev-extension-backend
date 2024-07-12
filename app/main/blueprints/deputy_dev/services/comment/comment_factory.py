from app.main.blueprints.deputy_dev.constants.repo import VCSTypes
from app.main.blueprints.deputy_dev.services.comment.base_comment import BaseComment
from app.main.blueprints.deputy_dev.services.comment.bitbucket_comment import (
    BitbucketComment,
)
from app.main.blueprints.deputy_dev.services.comment.github_comment import GithubComment


class CommentFactory:
    FACTORIES = {VCSTypes.bitbucket.value: BitbucketComment, VCSTypes.github.value: GithubComment}

    @classmethod
    async def comment(cls, vcs_type: str, workspace, repo_name, pr_id, pr_details) -> BaseComment:
        if vcs_type not in cls.FACTORIES:
            raise ValueError("Incorrect vcs type passed")
        _klass = cls.FACTORIES[vcs_type]
        _klass_obj = _klass(workspace=workspace, pr_id=pr_id, repo_name=repo_name, pr_details=pr_details)
        return _klass_obj
