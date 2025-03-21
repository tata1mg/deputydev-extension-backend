from deputydev_core.utils.context_vars import set_context_values

from app.backend_common.services.pr.base_pr import BasePR
from app.backend_common.services.pr.pr_factory import PRFactory
from app.backend_common.services.repo.base_repo import BaseRepo
from app.backend_common.services.repo.repo_factory import RepoFactory
from app.backend_common.services.workspace.context_var import identifier
from app.main.blueprints.deputy_dev.services.comment.comment_factory import (
    CommentFactory,
)
from app.main.blueprints.deputy_dev.utils import get_vcs_auth_handler


class BasePRReviewManager:
    @staticmethod
    def set_identifier(value: str):
        """Set repo_name or any other value to the contextvar identifier"""
        identifier.set(value)

    @classmethod
    def _set_context_values(cls, data: dict):
        cls.set_identifier(data.get("repo_name"))
        set_context_values(scm_pr_id=data.get("pr_id"), repo_name=data.get("repo_name"))

    @classmethod
    async def _get_auth_handler(cls, data: dict):
        """Get auth handler for VCS operations"""
        return await get_vcs_auth_handler(data.get("workspace_id"), data.get("vcs_type"))

    @classmethod
    async def initialize_repo_service(cls, data: dict, auth_handler=None):
        """Initialize repository service"""
        if not auth_handler:
            auth_handler = await cls._get_auth_handler(data)

        return await RepoFactory.repo(
            vcs_type=data.get("vcs_type"),
            repo_name=data.get("repo_name"),
            workspace=data.get("workspace"),
            workspace_id=data.get("workspace_id"),
            workspace_slug=data.get("workspace_slug"),
            auth_handler=auth_handler,
            repo_id=data.get("repo_id"),
        )

    @classmethod
    async def initialize_pr_service(cls, data: dict, repo_service: BaseRepo, auth_handler=None):
        """Initialize PR service"""
        if not auth_handler:
            auth_handler = await cls._get_auth_handler(data)

        return await PRFactory.pr(
            vcs_type=data.get("vcs_type"),
            repo_name=data.get("repo_name"),
            workspace=data.get("workspace"),
            workspace_id=data.get("workspace_id"),
            workspace_slug=data.get("workspace_slug"),
            auth_handler=auth_handler,
            pr_id=data.get("pr_id"),
            repo_service=repo_service,
            fetch_pr_details=True,
        )

    @classmethod
    async def initialize_comment_service(cls, data: dict, pr_service: BasePR, auth_handler=None):
        """Initialize comment service"""
        if not auth_handler:
            auth_handler = await cls._get_auth_handler(data)

        return await CommentFactory.initialize(
            vcs_type=data.get("vcs_type"),
            repo_name=data.get("repo_name"),
            pr_id=data.get("pr_id"),
            workspace=data.get("workspace"),
            workspace_slug=data.get("workspace_slug"),
            pr_details=pr_service.pr_details,
            auth_handler=auth_handler,
            repo_id=data.get("repo_id"),
        )

    @classmethod
    async def initialise_services(cls, data: dict):
        """Initialize all required services for PR operations"""
        cls._set_context_values(data)

        auth_handler = await cls._get_auth_handler(data)
        repo_service = await cls.initialize_repo_service(data, auth_handler)
        pr_service = await cls.initialize_pr_service(data, repo_service, auth_handler)
        comment_service = await cls.initialize_comment_service(data, pr_service, auth_handler)

        return repo_service, pr_service, comment_service
