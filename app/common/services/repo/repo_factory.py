from app.common.services.credentials.factory import AuthHandlerFactory
from app.common.services.repo.base_repo import BaseRepo
from app.common.services.repo.bitbucket_repo import BitbucketRepo
from app.common.services.repo.github_repo import GithubRepo
from app.common.services.repo.gitlab_repo import GitlabRepo
from app.common.services.repository.repo.repo_service import RepoService
from app.common.services.repository.workspace.main import WorkspaceService
from app.main.blueprints.deputy_dev.constants.repo import VCSTypes


class RepoFactory:
    FACTORIES = {
        VCSTypes.bitbucket.value: BitbucketRepo,
        VCSTypes.github.value: GithubRepo,
        VCSTypes.gitlab.value: GitlabRepo,
    }

    @classmethod
    async def repo(
        cls,
        vcs_type: str,
        workspace,
        repo_name,
        workspace_id,
        auth_handler,
        workspace_slug,
        repo_id=None,
    ) -> BaseRepo:
        if vcs_type not in cls.FACTORIES:
            raise ValueError("Incorrect vcs type passed")
        _klass = cls.FACTORIES[vcs_type]
        _klass_obj = _klass(
            workspace=workspace,
            repo_name=repo_name,
            workspace_id=workspace_id,
            workspace_slug=workspace_slug,
            auth_handler=auth_handler,
            repo_id=repo_id,
        )
        return _klass_obj

    @classmethod
    async def get_repo_by_id(cls, repo_id: int):
        repo = await RepoService.db_get(filters={"id": repo_id}, fetch_one=True)
        workspace = await WorkspaceService.db_get(filters={"id": repo.workspace_id}, fetch_one=True)
        return await cls.repo(
            vcs_type=repo.scm,
            workspace=workspace.name,
            repo_name=repo.name,
            workspace_id=repo.workspace_id,
            auth_handler=AuthHandlerFactory.create_vcs_auth_handler(workspace),
            workspace_slug=workspace.slug,
            repo_id=repo.id,
        )
