from torpedo import CONFIG

from app.common.utils.app_utils import convert_to_datetime
from app.main.blueprints.deputy_dev.constants.constants import (
    GithubActions,
    MetaStatCollectionTypes,
    PRStatus,
)
from app.main.blueprints.deputy_dev.constants.repo import VCSTypes
from app.main.blueprints.deputy_dev.services.sqs.meta_subscriber import MetaSubscriber
from app.main.blueprints.deputy_dev.services.webhook.human_comment_webhook import (
    HumanCommentWebhook,
)
from app.main.blueprints.deputy_dev.services.webhook.pr_approval_webhook import (
    PRApprovalWebhook,
)
from app.main.blueprints.deputy_dev.services.webhook.pullrequest_close_webhook import (
    PullRequestCloseWebhook,
)
from app.main.blueprints.deputy_dev.services.workspace.workspace_service import (
    WorkspaceService,
)
from app.main.blueprints.deputy_dev.utils import (
    is_request_from_blocked_repo,
    update_payload_with_jwt_data,
)


class StatsCollectionTrigger:
    config = CONFIG.config

    @classmethod
    async def select_stats_and_publish(cls, payload, query_params):
        parsed_payload = {}

        payload = update_payload_with_jwt_data(query_params, payload)
        vcs_type = payload.get("vcs_type")

        stats_type = cls.get_stats_collection_type(vcs_type, payload)
        if stats_type == MetaStatCollectionTypes.HUMAN_COMMENT.value:  # This is not being used
            parsed_payload = await HumanCommentWebhook.parse_payload(payload)
        elif stats_type == MetaStatCollectionTypes.PR_CLOSE.value:
            parsed_payload = await PullRequestCloseWebhook.parse_payload(payload)
        elif stats_type == MetaStatCollectionTypes.PR_APPROVAL_TIME.value:
            parsed_payload = await PRApprovalWebhook.parse_payload(payload)
        if stats_type and await cls.is_pr_created_post_onboarding(parsed_payload, vcs_type):

            data = {"payload": parsed_payload.dict(), "vcs_type": vcs_type, "stats_type": stats_type}
            if not is_request_from_blocked_repo(data["payload"].get("repo_name")):
                await MetaSubscriber(config=cls.config).publish(data)

    @classmethod
    def get_stats_collection_type(cls, vcs_type, payload):
        if vcs_type == VCSTypes.bitbucket.value:
            return cls.bitbucket_stat_type(payload)
        elif vcs_type == VCSTypes.github.value:
            return cls.github_stat_type(payload)
        elif vcs_type == VCSTypes.gitlab.value:
            return cls.gitlab_stat_type(payload)

    @classmethod
    def bitbucket_stat_type(cls, payload):
        if payload.get("pullrequest", {}).get("state") in [PRStatus.MERGED.value, PRStatus.DECLINED.value]:
            return MetaStatCollectionTypes.PR_CLOSE.value
        if payload.get("comment"):
            return MetaStatCollectionTypes.HUMAN_COMMENT.value
        if payload.get("approval"):
            return MetaStatCollectionTypes.PR_APPROVAL_TIME.value

    @classmethod
    def github_stat_type(cls, payload):
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
    def gitlab_stat_type(cls, payload):
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

    @classmethod
    async def is_pr_created_post_onboarding(cls, stats_webhook_payload, vcs_type):
        """
        Check if PR is created after onboarding time of team.
        Returns:
             bool: True if pr created after onboarding time else False.
        """
        pr_created_at = convert_to_datetime(stats_webhook_payload.pr_created_at)
        workspace_dto = await WorkspaceService.find(
            scm_workspace_id=stats_webhook_payload.scm_workspace_id, scm=vcs_type
        )
        if workspace_dto:
            if pr_created_at and pr_created_at > workspace_dto.created_at:
                return True
        return False
