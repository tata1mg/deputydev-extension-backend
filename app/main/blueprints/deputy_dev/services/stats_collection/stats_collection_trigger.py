from torpedo import CONFIG

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


class StatsCollectionTrigger:
    config = CONFIG.config

    @classmethod
    async def select_stats_and_publish(cls, payload, query_params):
        parsed_payload = {}
        vcs_type = query_params.get("vcs_type", VCSTypes.bitbucket.value)
        stats_type = cls.get_stats_collection_type(vcs_type, payload)
        if stats_type == MetaStatCollectionTypes.HUMAN_COMMENT.value:  # This is not being used
            parsed_payload = await HumanCommentWebhook.parse_payload(payload, vcs_type)
        elif stats_type == MetaStatCollectionTypes.PR_CLOSE.value:
            parsed_payload = await PullRequestCloseWebhook.parse_payload(payload, vcs_type)
        elif stats_type == MetaStatCollectionTypes.PR_APPROVAL_TIME.value:
            parsed_payload = await PRApprovalWebhook.parse_payload(payload, vcs_type)
        if stats_type:
            data = {"payload": parsed_payload.dict(), "query_params": query_params, "stats_type": stats_type}
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
