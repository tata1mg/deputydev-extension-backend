from app.main.blueprints.deputy_dev.constants.repo import VCSTypes
from app.main.blueprints.deputy_dev.services.repo.base_repo import BaseRepo
from app.main.blueprints.deputy_dev.services.repo.bitbucket_repo import BitbucketRepo
from app.main.blueprints.deputy_dev.services.repo.github_repo import GithubRepo
from app.main.blueprints.deputy_dev.services.repo.gitlab_repo import GitlabRepo


class RepoFactory:
    FACTORIES = {
        VCSTypes.bitbucket.value: BitbucketRepo,
        VCSTypes.github.value: GithubRepo,
        VCSTypes.gitlab.value: GitlabRepo,
    }

    @classmethod
    async def repo(
        cls, vcs_type: str, workspace, repo_name, pr_id, workspace_id, auth_handler, workspace_slug, repo_id=None
    ) -> BaseRepo:
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
            repo_id=repo_id,
        )
        await _klass_obj.initialize()
        return _klass_obj
