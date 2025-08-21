from app.backend_common.constants.constants import VCSTypes
from app.backend_common.repository.repo.repository import RepoRepository
from app.backend_common.repository.workspace.main import WorkspaceService
from app.backend_common.services.credentials.auth_handler import AuthHandler
from app.backend_common.services.credentials.factory import AuthHandlerFactory
from app.backend_common.services.repo.base_repo import BaseRepo
from app.backend_common.services.repo.bitbucket_repo import BitbucketRepo
from app.backend_common.services.repo.github_repo import GithubRepo
from app.backend_common.services.repo.gitlab_repo import GitlabRepo


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
        workspace: str,
        repo_name: str,
        workspace_id: int,
        auth_handler: AuthHandler,
        workspace_slug: str,
        repo_id: int | None = None,
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
    async def get_repo_by_workspace_id_and_name(cls, workspace_id: int, repo_name: str) -> BaseRepo:
        workspace = await WorkspaceService.db_get(filters={"id": workspace_id}, fetch_one=True)
        return await cls.repo(
            vcs_type=workspace.scm,
            workspace=workspace.name,
            repo_name=repo_name,
            workspace_id=workspace_id,
            auth_handler=AuthHandlerFactory.create_vcs_auth_handler(workspace),
            workspace_slug=workspace.slug,
        )

    @classmethod
    async def get_repo_by_id(cls, repo_id: int) -> BaseRepo:
        repo = await RepoRepository.db_get(filters={"id": repo_id}, fetch_one=True)
        workspace = await WorkspaceService.db_get(filters={"id": repo.workspace_id}, fetch_one=True)
        return await cls.repo(
            vcs_type=repo.scm,
            workspace=workspace.name,
            repo_name=repo.name,
            workspace_id=repo.workspace_id,
            auth_handler=AuthHandlerFactory.create_vcs_auth_handler(workspace),
            workspace_slug=workspace.slug,
            repo_id=repo.scm_repo_id,
        )

    @classmethod
    def get_vcs_host(cls, vcs_type: str) -> str:
        return cls.FACTORIES[vcs_type].get_remote_host()
