import asyncio
from typing import Any, Dict, Optional

from app.backend_common.constants.constants import PRStatus, VCSTypes
from app.backend_common.services.repo.base_repo import BaseRepo
from app.backend_common.services.repo.repo_factory import RepoFactory
from app.backend_common.services.workspace.workspace_service import WorkspaceService
from app.backend_common.utils.app_utils import convert_to_datetime
from app.backend_common.utils.sanic_wrapper import CONFIG
from app.main.blueprints.deputy_dev.constants.constants import (
    GithubActions,
    MetaStatCollectionTypes,
)
from app.main.blueprints.deputy_dev.services.message_queue.factories.message_queue_factory import (
    MessageQueueFactory,
)
from app.main.blueprints.deputy_dev.services.repository.pr.pr_service import PRService
from app.main.blueprints.deputy_dev.services.setting.setting_service import (
    SettingService,
)
from app.main.blueprints.deputy_dev.services.webhook.human_comment_webhook import (
    HumanCommentWebhook,
)
from app.main.blueprints.deputy_dev.services.webhook.pr_approval_webhook import (
    PRApprovalWebhook,
)
from app.main.blueprints.deputy_dev.services.webhook.pullrequest_close_webhook import (
    PullRequestCloseWebhook,
)
from app.main.blueprints.deputy_dev.utils import (
    get_vcs_auth_handler,
    is_request_from_blocked_repo,
    update_payload_with_jwt_data,
)


class StatsCollectionTrigger:
    config = CONFIG.config

    def __init__(self, repo_service: Optional[BaseRepo] = None) -> None:
        self.repo_service = repo_service
        self.default_branch = None
        self.workspace = None

    async def select_stats_and_publish(self, payload: Dict[str, Any], query_params: Dict[str, Any]) -> None:
        parsed_payload = {}
        payload = update_payload_with_jwt_data(query_params, payload)
        vcs_type = payload.get("vcs_type")
        stats_type = self.get_stats_collection_type(vcs_type, payload)
        if stats_type == MetaStatCollectionTypes.HUMAN_COMMENT.value:  # This is not being used
            parsed_payload = await HumanCommentWebhook.parse_payload(payload)
        elif stats_type == MetaStatCollectionTypes.PR_CLOSE.value:
            parsed_payload = await PullRequestCloseWebhook.parse_payload(payload)
        elif stats_type == MetaStatCollectionTypes.PR_APPROVAL_TIME.value:
            parsed_payload = await PRApprovalWebhook.parse_payload(payload)
        if not parsed_payload:
            return
        if stats_type and await self.is_pr_created_post_onboarding(parsed_payload, vcs_type):
            data = {"payload": parsed_payload.dict(), "vcs_type": vcs_type, "stats_type": stats_type}
            if not is_request_from_blocked_repo(data["payload"].get("repo_name")):
                self.repo_service = await self.repo_instance(parsed_payload, vcs_type)
                if (
                    stats_type == MetaStatCollectionTypes.PR_CLOSE.value
                    and parsed_payload.pr_state == PRStatus.MERGED.value
                ):
                    asyncio.create_task(self.update_repo_setting(parsed_payload, vcs_type))
                is_eligible_for_review = await self.is_repo_eligible_for_review()
                if is_eligible_for_review or await PRService.fetch_pr(
                    scm_workspace_id=parsed_payload.scm_workspace_id,
                    repo_name=parsed_payload.repo_name,
                    scm=vcs_type,
                    scm_pr_id=parsed_payload.scm_repo_id,
                ):
                    await MessageQueueFactory.meta_subscriber()(config=self.config).publish(data)

    @classmethod
    async def repo_instance(cls, payload: Any, vcs_type: str) -> BaseRepo:
        auth_handler = await get_vcs_auth_handler(payload.scm_workspace_id, vcs_type)
        repo = await RepoFactory.repo(
            vcs_type=vcs_type,
            repo_name=payload.repo_name,
            workspace=payload.workspace,
            workspace_slug=payload.workspace_slug,
            workspace_id=payload.scm_workspace_id,
            repo_id=payload.scm_repo_id,
            auth_handler=auth_handler,
        )
        return repo

    async def update_repo_setting(self, parsed_payload: Any, vcs_type: str) -> None:
        self.default_branch = await self.repo_service.get_default_branch()
        if self.default_branch == parsed_payload.destination_branch:
            await SettingService(self.repo_service, self.workspace.team_id, self.default_branch).update_repo_setting()

    @classmethod
    def get_stats_collection_type(cls, vcs_type: str, payload: Dict[str, Any]) -> Optional[str]:
        if vcs_type == VCSTypes.bitbucket.value:
            return cls.bitbucket_stat_type(payload)
        elif vcs_type == VCSTypes.github.value:
            return cls.github_stat_type(payload)
        elif vcs_type == VCSTypes.gitlab.value:
            return cls.gitlab_stat_type(payload)

    @classmethod
    def bitbucket_stat_type(cls, payload: Dict[str, Any]) -> Optional[str]:
        if payload.get("pullrequest", {}).get("state") in [PRStatus.MERGED.value, PRStatus.DECLINED.value]:
            return MetaStatCollectionTypes.PR_CLOSE.value
        if payload.get("comment"):
            return MetaStatCollectionTypes.HUMAN_COMMENT.value
        if payload.get("approval"):
            return MetaStatCollectionTypes.PR_APPROVAL_TIME.value

    @classmethod
    def github_stat_type(cls, payload: Dict[str, Any]) -> Optional[str]:
        if payload.get("action") == GithubActions.CLOSED.value and "merged" in payload.get("pull_request", {}):
            return MetaStatCollectionTypes.PR_CLOSE.value
        if payload.get("action") == GithubActions.CREATED.value and payload.get("comment"):
            return MetaStatCollectionTypes.HUMAN_COMMENT.value
        if (
            payload.get("action") == GithubActions.SUBMITTED.value
            and payload.get("review", {}).get("state") == PRStatus.APPROVED.value
        ):
            return MetaStatCollectionTypes.PR_APPROVAL_TIME.value

    @classmethod
    def gitlab_stat_type(cls, payload: Dict[str, Any]) -> Optional[str]:
        if payload.get("object_kind") == "merge_request":
            action = payload.get("object_attributes", {}).get("state")
            if action.lower() in [PRStatus.MERGED.value.lower(), PRStatus.DECLINED.value.lower()]:
                return MetaStatCollectionTypes.PR_CLOSE.value
        elif payload.get("object_kind") == "note":
            noteable_type = payload.get("object_attributes", {}).get("noteable_type")
            if noteable_type == "MergeRequest" and payload.get("object_attributes", {}).get("action") == "create":
                return MetaStatCollectionTypes.HUMAN_COMMENT.value
        elif (
            payload.get("object_kind") == "merge_request"
            and payload.get("object_attributes", {}).get("approval_state") == PRStatus.APPROVED.value
        ):
            return MetaStatCollectionTypes.PR_APPROVAL_TIME.value
        else:
            return None

    async def is_pr_created_post_onboarding(self, stats_webhook_payload: Any, vcs_type: str) -> bool:
        """
        Check if PR is created after onboarding time of team.
        Returns:
             bool: True if pr created after onboarding time else False.
        """
        pr_created_at = convert_to_datetime(stats_webhook_payload.pr_created_at)
        workspace_dto = await WorkspaceService.find(
            scm_workspace_id=stats_webhook_payload.scm_workspace_id, scm=vcs_type
        )
        self.workspace = workspace_dto
        if workspace_dto:
            if pr_created_at and pr_created_at > workspace_dto.created_at:
                return True
        return False

    async def is_repo_eligible_for_review(self) -> bool:
        # HACK: This is done temporarily for fixing latency  issue
        return True
