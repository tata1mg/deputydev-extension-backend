from app.common.services.pr.base_pr import BasePR
from app.common.services.pr.vcs_pr_handlers.bitbucket_pr import BitbucketPR
from app.common.services.pr.vcs_pr_handlers.github_pr import GithubPR
from app.common.services.pr.vcs_pr_handlers.gitlab_pr import GitlabPR
from app.common.services.repo.base_repo import BaseRepo
from app.main.blueprints.deputy_dev.constants.repo import VCSTypes


class PRFactory:
    FACTORIES = {
        VCSTypes.bitbucket.value: BitbucketPR,
        VCSTypes.github.value: GithubPR,
        VCSTypes.gitlab.value: GitlabPR,
    }

    @classmethod
    async def pr(
        cls,
        vcs_type: str,
        workspace,
        repo_name,
        pr_id,
        workspace_id,
        auth_handler,
        workspace_slug,
        repo_service: BaseRepo,
        fetch_pr_details=False,
    ) -> BasePR:
        if vcs_type not in cls.FACTORIES:
            raise ValueError("Incorrect vcs type passed")
        _klass = cls.FACTORIES[vcs_type]
        _klass_obj = _klass(
            workspace=workspace,
            pr_id=pr_id,
            repo_name=repo_name,
            workspace_id=workspace_id,
            workspace_slug=workspace_slug,
            auth_handler=auth_handler,
            repo_service=repo_service,
        )
        if fetch_pr_details:
            await _klass_obj.initialize()
        return _klass_obj
