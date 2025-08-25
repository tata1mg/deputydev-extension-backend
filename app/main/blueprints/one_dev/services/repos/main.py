from typing import Dict

from app.backend_common.models.dto.workspace_dto import WorkspaceDTO
from app.backend_common.repository.workspace.main import WorkspaceService
from app.backend_common.services.repo.repo_factory import RepoFactory


class ReposHandler:
    @classmethod
    def _get_generic_repo_url(cls, vcs_type: str, workspace_slug: str, repo_name: str) -> str:
        return f"git@{RepoFactory.get_vcs_host(vcs_type)}:{workspace_slug}/{repo_name}.git"

    @classmethod
    async def get_registered_repo_details(
        cls, repo_name: str, vcs_type: str, workspace_slug: str
    ) -> Dict[str, str | int | None]:
        workspace = await WorkspaceService.db_get(filters=dict(scm=vcs_type, slug=workspace_slug), fetch_one=True)
        if not workspace or not isinstance(workspace, WorkspaceDTO) or not workspace.slug:
            return dict(repo_url=None, workspace_id=None)

        return dict(
            repo_url=cls._get_generic_repo_url(vcs_type=vcs_type, workspace_slug=workspace.slug, repo_name=repo_name),
            workspace_id=workspace.id,
        )
