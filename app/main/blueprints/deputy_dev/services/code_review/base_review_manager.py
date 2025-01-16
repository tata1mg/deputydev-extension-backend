from app.backend_common.services.pr.pr_factory import PRFactory
from app.backend_common.services.repo.repo_factory import RepoFactory
from app.backend_common.services.workspace.context_var import identifier
from app.common.utils.context_vars import set_context_values
from app.main.blueprints.deputy_dev.models.chat_request import ChatRequest
from app.main.blueprints.deputy_dev.services.comment.comment_factory import (
    CommentFactory,
)
from app.main.blueprints.deputy_dev.utils import get_vcs_auth_handler


class BaseReviewManager:
    @staticmethod
    def set_identifier(value: str):
        """Set repo_name or any other value to the contextvar identifier

        Args:
            value (str): value to set for the identifier
        """
        identifier.set(value)

    @classmethod
    async def initialise_services(cls, data: dict):
        """Initialize required services for PR operations"""

        cls.set_identifier(data.get("repo_name"))  # need to deprecate
        set_context_values(scm_pr_id=data.get("pr_id"), repo_name=data.get("repo_name"))
        vcs_type = data.get("vcs_type")
        repo_name, pr_id, workspace, scm_workspace_id, repo_id, workspace_slug = (
            data.get("repo_name"),
            data.get("pr_id"),
            data.get("workspace"),
            data.get("workspace_id"),
            data.get("repo_id"),
            data.get("workspace_slug"),
        )

        auth_handler = await get_vcs_auth_handler(scm_workspace_id, vcs_type)

        repo_service = await RepoFactory.repo(
            vcs_type=vcs_type,
            repo_name=repo_name,
            workspace=workspace,
            workspace_id=scm_workspace_id,
            workspace_slug=workspace_slug,
            auth_handler=auth_handler,
            repo_id=repo_id,
        )

        pr_service = await PRFactory.pr(
            vcs_type=vcs_type,
            repo_name=repo_name,
            workspace=workspace,
            workspace_id=scm_workspace_id,
            workspace_slug=workspace_slug,
            auth_handler=auth_handler,
            pr_id=pr_id,
            repo_service=repo_service,
            fetch_pr_details=True,
        )

        comment_service = await CommentFactory.initialize(
            vcs_type=vcs_type,
            repo_name=repo_name,
            pr_id=pr_id,
            workspace=workspace,
            workspace_slug=workspace_slug,
            pr_details=pr_service.pr_details,
            auth_handler=auth_handler,
            repo_id=repo_id,
        )

        return repo_service, pr_service, comment_service

    @staticmethod
    def _prepare_service_data_from_chat_request(chat_request: ChatRequest) -> dict:
        return {
            "vcs_type": chat_request.repo.vcs_type,
            "repo_name": chat_request.repo.repo_name,
            "pr_id": chat_request.repo.pr_id,
            "workspace": chat_request.repo.workspace,
            "workspace_id": chat_request.repo.workspace_id,
            "repo_id": chat_request.repo.repo_id,
            "workspace_slug": chat_request.repo.workspace_slug,
        }
