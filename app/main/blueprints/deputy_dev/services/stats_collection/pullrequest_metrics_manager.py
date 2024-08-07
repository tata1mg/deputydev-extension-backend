from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from sanic.log import logger
from torpedo import CONFIG

from app.common.exception import RetryException
from app.main.blueprints.deputy_dev.constants.constants import (
    BitbucketBots,
    PrStatusTypes,
)
from app.main.blueprints.deputy_dev.services.chat.pre_processors.comment_pre_processer import CommentPreprocessor
from app.main.blueprints.deputy_dev.services.experiment.experiment_service import (
    ExperimentService,
)
from app.main.blueprints.deputy_dev.services.pr.pr_service import PRService
from app.main.blueprints.deputy_dev.services.repo.repo_factory import RepoFactory
from app.main.blueprints.deputy_dev.services.repo.repo_service import RepoService
from app.main.blueprints.deputy_dev.services.webhook.pullrequest_close_webhook import PullRequestCloseWebhook
from app.main.blueprints.deputy_dev.services.workspace.workspace_service import (
    WorkspaceService,
)


class PullRequestMetricsManager:
    def __init__(self, payload, vcs_type):
        self.payload = payload
        self.vcs_type = vcs_type
        self.pr_close_payload = PullRequestCloseWebhook.parse_payload(payload, vcs_type)
        self.repo_service = None
        self.workspace_dto = None
        self.repo_dto = None
        self.pr_dto = None
        self.sqs_message_retention_time = CONFIG.config.get("SQS", {}).get("MESSAGE_RETENTION_TIME_SEC", 0)
        self.experiment_start_time = datetime.fromisoformat(CONFIG.config.get("EXPERIMENT_START_TIME"))

    @classmethod
    async def handle_event(cls, data: Dict[str, Any]) -> None:
        logger.info("Received SQS Message metasync: {}".format(data))
        payload = data.get("payload")
        query_params = data.get("query_params") or {}
        manager = PullRequestMetricsManager(payload, query_params.get("vcs_type", "bitbucket"))
        await manager.compute_pr_close_metrics()

    async def compute_pr_close_metrics(self):
        logger.info(f"PR close paylod: {self.pr_close_payload}")
        await self.initialize_repo_service()
        await self.initialize_workspace_and_repo_dto()
        await self.initialize_pr_dto()

        if not self.pr_dto and self.pr_close_payload["pr_created_at"] > self.experiment_start_time:
            raise RetryException(f"PR: {self.pr_close_payload['pr_id']} not picked to be reviewed by Deputydev")

        pr_time_since_creation = (
            datetime.now(timezone.utc) - self.pr_dto.scm_creation_time.astimezone(timezone.utc)
        ).total_seconds()

        if (
            self.pr_dto.review_status == PrStatusTypes.FAILED.value
            and pr_time_since_creation < self.sqs_message_retention_time
        ):
            raise RetryException(
                f"PR: {self.pr_close_payload['pr_id']} is in sqs and still have a chance to be reviewed by Deputydev"
            )

        if self.pr_dto.review_status == PrStatusTypes.IN_PROGRESS.value:
            raise RetryException(
                f"PR: {self.pr_close_payload['pr_id']} is still in progress to be reviewed by Deputydev"
            )

        if self.pr_dto.review_status not in [PrStatusTypes.COMPLETED.value, PrStatusTypes.REJECTED_EXPERIMENT.value]:
            # For not completed or not rejected experiment we will just be updating the pr state of both experiments and pull request
            # table without updating comment count.
            await PRService.db_update(
                payload={
                    "pr_state": self.pr_close_payload["pr_state"],
                    "scm_close_time": self.pr_close_payload["pr_closed_at"],
                },
                filters={"repo_id": self.repo_dto.id, "scm_pr_id": self.pr_close_payload["pr_id"]},
            )
            return

        all_comments = await self.repo_service.get_pr_comments()
        llm_comment_count, human_comment_count = self.count_bot_and_human_comments(all_comments)

        close_cycle_time = await self.calculate_pr_close_cycle_time()

        await self.post_pr_close_processing(llm_comment_count, human_comment_count, close_cycle_time)

    async def initialize_pr_dto(self):
        """
        Initializes the PR DTO.
        """
        self.pr_dto = await PRService.db_get(
            {
                "repo_id": self.repo_dto.id,
                "workspace_id": self.workspace_dto.id,
                "scm_pr_id": self.pr_close_payload["pr_id"],
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
        if not self.workspace_dto:
            raise RetryException(f"Workspace not found in DB: SCM Workspace ID : {pr_model.scm_workspace_id()}")
        self.repo_dto = await RepoService.find(scm_repo_id=pr_model.scm_repo_id(), workspace_id=self.workspace_dto.id)
        if not self.repo_dto:
            raise RetryException(
                f"PR: {self.pr_close_payload['pr_id']} not picked to be reviewed by Deputydev. Reason: Repository does not exist in our DB."
            )

    async def initialize_repo_service(self):
        """
        Retrieves the repository instance based on the given VCS type and payload.
        """
        repo_name = self.pr_close_payload.get("repo_name")
        pr_id = self.pr_close_payload.get("pr_id")
        workspace = self.pr_close_payload.get("workspace")
        scm_workspace_id = self.pr_close_payload.get("workspace_id")

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
        tags_list = CommentPreprocessor.combine_comments_enums()
        for comment in comments:
            if comment.get("parent") is None:
                if comment.get("user", {}).get("display_name") in chat_authors:
                    # There are many bots that are currently running in bitbucket, but we are only considering
                    # the comment from DeputyDev for llm count, rest of the bot comment counts are ignored
                    if comment.get("user", {}).get("display_name") == BitbucketBots.DEPUTY_DEV.value:
                        bot_comment_count += 1
                else:
                    # Any tags such as #scrit, #like or any other whitelisted tags we receive starts with
                    # \#dd, \#scrit, that is why we are filtering out this tags starting with "\"
                    if not any(comment.get("content").get("raw").lower().startswith(f"\{tag}") for tag in tags_list):
                        human_comment_count += 1

        return bot_comment_count, human_comment_count

    async def post_pr_close_processing(self, llm_comment_count, human_comment_count, close_cycle_time):

        await PRService.db_update(
            payload={
                "scm_close_time": self.pr_close_payload["pr_closed_at"],
                "pr_state": self.pr_close_payload["pr_state"],
            },
            filters={"repo_id": self.repo_dto.id, "scm_pr_id": self.pr_close_payload["pr_id"]},
        )
        await ExperimentService.db_update(
            payload={
                "scm_close_time": self.pr_close_payload["pr_closed_at"],
                "llm_comment_count": llm_comment_count,
                "human_comment_count": human_comment_count,
                "close_time_in_sec": close_cycle_time,
                "pr_state": self.pr_close_payload["pr_state"],
            },
            filters={"pr_id": self.pr_dto.id},
        )

    async def calculate_pr_close_cycle_time(self):
        """
        Calculates the stats_collection cycle time from the provided payload and VCS type, then stores it.
        """
        pr_created_at = self.pr_close_payload["pr_created_at"]
        pr_closed_at = self.pr_close_payload["pr_closed_at"]

        created_time_epoch = int(pr_created_at.timestamp())
        pr_close_time_epoch = int(pr_closed_at.timestamp())

        cycle_time_seconds = pr_close_time_epoch - created_time_epoch

        return cycle_time_seconds
