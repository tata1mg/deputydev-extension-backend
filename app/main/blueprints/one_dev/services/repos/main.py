from app.common.services.credentials.factory import AuthHandlerFactory
from app.common.services.repo.repo_factory import RepoFactory
from app.common.services.repository.repo.repo_service import RepoService
from app.common.services.repository.workspace.main import WorkspaceService


class ReposHandler:
    @classmethod
    async def get_registered_repo_details(cls, repo_name: str, vcs_type: str, team_id: int):
        workspaces = await WorkspaceService.db_get(filters=dict(team_id=team_id))
        workspace_ids = [workspace.id for workspace in workspaces]
        repos = await RepoService.db_get(filters=dict(workspace_id__in=workspace_ids))
        for repo in repos:
            if repo.name == repo_name and repo.scm == vcs_type:
                repo_id = repo.id
                workspace = next(workspace for workspace in workspaces if workspace.id == repo.workspace_id)
                registered_repo = await RepoFactory.repo(
                    vcs_type=repo.scm,
                    workspace=workspace.name,
                    repo_name=repo.name,
                    workspace_id=repo.workspace_id,
                    auth_handler=AuthHandlerFactory.create_vcs_auth_handler(workspace),
                    workspace_slug=workspace.slug,
                    repo_id=repo.id,
                )

                return dict(
                    repo_id=repo_id,
                    repo_url=registered_repo.get_remote_url_without_token(),
                )

        return dict(repo_id=None, repo_url=None)
