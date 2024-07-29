from typing import Dict, List, Tuple, Any
from datetime import datetime, timezone
from torpedo import CONFIG
from sanic.log import logger

from app.common.exception import RetryException
from app.main.blueprints.deputy_dev.constants.constants import (
    BitbucketBots,
    PrStatusTypes,
)
from app.main.blueprints.deputy_dev.services.experiment.experiment_service import (
    ExperimentService,
)
from app.main.blueprints.deputy_dev.services.pr.pr_service import PRService
from app.main.blueprints.deputy_dev.services.repo.repo_factory import RepoFactory
from app.main.blueprints.deputy_dev.services.repo.repo_service import RepoService
from app.main.blueprints.deputy_dev.services.webhook.merge_webhook import MergeWebhook
from app.main.blueprints.deputy_dev.services.workspace.workspace_service import (
    WorkspaceService,
)


class MergeMetricsManager:
    def __init__(self, payload, vcs_type):
        self.payload = payload
        self.vcs_type = vcs_type
        self.merge_payload = MergeWebhook.parse_payload(payload, vcs_type)
        self.repo_service = None
        self.workspace_dto = None
        self.repo_dto = None
        self.pr_dto = None
        self.sqs_message_retention_time = CONFIG.config.get("SQS", {}).get("MESSAGE_RETENTION_TIME_SEC", 0)

    @classmethod
    async def handle_event(cls, data: Dict[str, Any]) -> None:
        logger.info("Received SQS Message metasync: {}".format(data))
        payload = data.get("payload")
        query_params = data.get("query_params") or {}
        manager = MergeMetricsManager(payload, query_params.get("vcs_type", "bitbucket"))
        await manager.compute_merge_metrics()

    async def compute_merge_metrics(self):
        await self.initialize_repo_service()
        await self.initialize_workspace_and_repo_dto()
        await self.initialize_pr_dto()

        if not self.pr_dto:
            raise RetryException(f"PR: {self.merge_payload['pr_id']} not picked to be reviewed by Deputydev")

        pr_time_since_creation = (
            datetime.now(timezone.utc) - self.pr_dto.scm_creation_time.astimezone(timezone.utc)
        ).total_seconds()

        if (
            self.pr_dto.review_status == PrStatusTypes.FAILED.value
            and pr_time_since_creation < self.sqs_message_retention_time
        ):
            raise RetryException(
                f"PR: {self.merge_payload['pr_id']} is in sqs and still have a chance to be reviewed by Deputydev"
            )

        if self.pr_dto.review_status == PrStatusTypes.IN_PROGRESS.value:
            raise RetryException(f"PR: {self.merge_payload['pr_id']} is still in progress to be reviewed by Deputydev")

        if self.pr_dto.review_status not in [PrStatusTypes.COMPLETED.value, PrStatusTypes.REJECTED_EXPERIMENT.value]:
            return

        all_comments = await self.repo_service.get_pr_comments()
        llm_comment_count, human_comment_count = self.count_bot_and_human_comments(all_comments)

        merge_cycle_time = await self.calculate_merge_cycle_time()

        await self.post_merge_processing(llm_comment_count, human_comment_count, merge_cycle_time)

    async def initialize_pr_dto(self):
        """
        Initializes the PR DTO.
        """
        self.pr_dto = await PRService.db_get(
            {
                "repo_id": self.repo_dto.id,
                "workspace_id": self.workspace_dto.id,
                "scm_pr_id": self.merge_payload["pr_id"],
            }
        )

    async def initialize_workspace_and_repo_dto(self):
        """
        Initializes the workspace and repository DTOs.
        """
        pr_model = self.repo_service.pr_model()
        self.workspace_dto = await WorkspaceService.find(
            scm=pr_model.scm_type(),
            scm_workspace_id=pr_model.scm_workspace_id(),
        )
        self.repo_dto = await RepoService.find(scm_repo_id=pr_model.scm_repo_id(), workspace_id=self.workspace_dto.id)

    async def initialize_repo_service(self):
        """
        Retrieves the repository instance based on the given VCS type and payload.
        """
        repo_name = self.merge_payload.get("repo_name")
        pr_id = self.merge_payload.get("pr_id")
        workspace = self.merge_payload.get("workspace")
        scm_workspace_id = self.merge_payload.get("workspace_id")

        self.repo_service = await RepoFactory.repo(
            vcs_type=self.vcs_type, repo_name=repo_name, pr_id=pr_id, workspace=workspace, workspace_id=scm_workspace_id
        )

    @staticmethod
    def count_bot_and_human_comments(comments: List[Dict]) -> Tuple[int, int]:
        """
        Count the number of comments made by the bot and others.

        Args:
            comments (List[Dict]): List of comments from Bitbucket.

        Returns:
            Tuple[int, int]: Tuple containing two integers - count of bot comments and count of other comments.
        """
        chat_authors = BitbucketBots.list()
        bot_comment_count = 0
        human_comment_count = 0

        for comment in comments:
            if comment.get("parent") is None:
                if comment.get("user", {}).get("display_name") in chat_authors:
                    bot_comment_count += 1
                else:
                    human_comment_count += 1

        return bot_comment_count, human_comment_count

    async def post_merge_processing(self, llm_comment_count, human_comment_count, merge_cycle_time):

        await PRService.db_update(
            payload={"scm_merge_time": self.merge_payload["pr_merged_at"]},
            filters={"repo_id": self.repo_dto.id, "scm_pr_id": self.merge_payload["pr_id"]},
        )
        await ExperimentService.db_update(
            payload={
                "scm_merge_time": self.merge_payload["pr_merged_at"],
                "llm_comment_count": llm_comment_count,
                "human_comment_count": human_comment_count,
                "merge_time_in_sec": merge_cycle_time,
            },
            filters={"pr_id": self.pr_dto.id},
        )

    async def calculate_merge_cycle_time(self):
        """
        Calculates the stats_collection cycle time from the provided payload and VCS type, then stores it.
        """
        pr_created_at = self.merge_payload["pr_created_at"]
        pr_merged_at = self.merge_payload["pr_merged_at"]

        created_time_epoch = int(pr_created_at.timestamp())
        merged_time_epoch = int(pr_merged_at.timestamp())

        cycle_time_seconds = merged_time_epoch - created_time_epoch

        return cycle_time_seconds
