from sanic.log import logger
from app.common.service_clients.bitbucket.bitbucket_repo_client import (
    BitbucketRepoClient,
)
from app.main.blueprints.deputy_dev.constants.constants import (
    PrStatusTypes,
)
from app.common.utils.app_utils import convert_string, convert_to_datetime
from app.main.blueprints.deputy_dev.services.experiment.experiment_service import ExperimentService
from app.main.blueprints.deputy_dev.services.pr.pr_service import PRService
from app.main.blueprints.deputy_dev.services.repo.repo_service import RepoService
from app.main.blueprints.deputy_dev.services.stats_collection.pullrequest_metrics_manager import (
    PullRequestMetricsManager,
)
from app.main.blueprints.deputy_dev.utils import get_approval_time_from_participants_bitbucket


class BackfillManager:
    def __init__(self):
        self.bitbucket_client = None

    async def backfill_comments_count_in_experiments_table(self, query_params):
        pr_rows = await PRService.get_bulk_prs_by_filter(query_params)
        for pr in pr_rows:
            scm_pr_id = pr["scm_pr_id"]
            repo_id = pr["repo_id"]
            repo_dto = await RepoService.db_get({"id": repo_id})
            experiment_dto = await ExperimentService.db_get({"pr_id": pr["id"]})
            if repo_dto and experiment_dto:
                self.bitbucket_client = BitbucketRepoClient("tata1mg", convert_string(repo_dto.name), scm_pr_id)
                all_comments = await self.bitbucket_client.get_pr_comments()
                llm_comment_count, human_comment_count = PullRequestMetricsManager.count_bot_and_human_comments(
                    all_comments
                )
                # Ideally we should be doing this update in batches, but since we have less thand 450 data in experiment
                # table as of the time of adding this comment, we can do this one by one for now.
                await ExperimentService.db_update(
                    payload={"human_comment_count": human_comment_count, "llm_comment_count": llm_comment_count},
                    filters={"pr_id": pr["id"]},
                )
                logger.info(f"Backfilling of comment counts completed for - {pr['id']}")

    async def backfill_expermients_data(self, query_params):
        """
        Backfill experiment and pull request data based on the given query parameters.

        Args:
            query_params: The query parameters containing start and end date for data retrieval.
        """
        exp_rows = await ExperimentService.get_data_in_range(query_params.get("start"), query_params.get("end"))
        for row in exp_rows:
            repo_dto = await RepoService.db_get({"id": row.repo_id})
            pr_dto = await PRService.db_get({"id": row.pr_id})
            if repo_dto and pr_dto:
                # We will be fetching the PR details for every row in the table to backfill pr_state for each row
                self.bitbucket_client = BitbucketRepoClient("tata1mg", convert_string(repo_dto.name), pr_dto.scm_pr_id)
                pr_detail = await self.bitbucket_client.get_pr_details()
                if row.scm_close_time is None and row.close_time_in_sec is None:
                    if pr_detail["state"] == "MERGED" or pr_detail["state"] == "DECLINED":
                        all_comments = await self.bitbucket_client.get_pr_comments()
                        llm_comment_count, human_comment_count = PullRequestMetricsManager.count_bot_and_human_comments(
                            all_comments
                        )

                        if pr_dto.review_status not in [
                            PrStatusTypes.COMPLETED.value,
                            PrStatusTypes.REJECTED_EXPERIMENT.value,
                        ]:
                            await PRService.db_update(
                                payload={
                                    "pr_state": pr_detail["state"],
                                    "scm_close_time": convert_to_datetime(pr_detail["updated_on"]),
                                },
                                filters={"id": pr_dto.id},
                            )
                        else:
                            pr_created_at = row.scm_creation_time
                            pr_closed_at = convert_to_datetime(pr_detail["updated_on"])

                            created_time_epoch = int(pr_created_at.timestamp())
                            pr_close_time_epoch = int(pr_closed_at.timestamp())

                            cycle_time_seconds = pr_close_time_epoch - created_time_epoch

                            await ExperimentService.db_update(
                                payload={
                                    "human_comment_count": human_comment_count,
                                    "llm_comment_count": llm_comment_count,
                                    "close_time_in_sec": cycle_time_seconds,
                                    "scm_close_time": pr_closed_at,
                                    "pr_state": pr_detail["state"],
                                },
                                filters={"id": row.id},
                            )
                            await PRService.db_update(
                                payload={"scm_close_time": pr_closed_at, "pr_state": pr_detail["state"]},
                                filters={"id": pr_dto.id},
                            )
                        logger.info(f"Marked data to merge / decline state for experiment and PR for row - {row.id}")
                    else:
                        await ExperimentService.db_update(
                            payload={
                                "pr_state": pr_detail["state"],
                            },
                            filters={"id": row.id},
                        )
                        await PRService.db_update(
                            payload={"pr_state": pr_detail["state"]},
                            filters={"id": pr_dto.id},
                        )
                        logger.info(f"Marked data to open state for experiment and PR for row - {row.id}")
                else:
                    await ExperimentService.db_update(
                        payload={
                            "pr_state": pr_detail["state"],
                        },
                        filters={"id": row.id},
                    )
                    await PRService.db_update(
                        payload={"pr_state": pr_detail["state"]},
                        filters={"id": pr_dto.id},
                    )
                    logger.info(f"Marked data to merge state for experiment and PR for row - {row.id}")

    async def backfill_pullrequests_data(self, query_params):
        """
        Backfill pull request data based on the given query parameters.

        Args:
            query_params: The query parameters containing start and end date for data retrieval.
        """
        pr_rows = await PRService.get_bulk_prs_by_filter(query_params)
        for row in pr_rows:
            if row["pr_state"] is None:
                repo_dto = await RepoService.db_get({"id": row["repo_id"]})
                self.bitbucket_client = BitbucketRepoClient("tata1mg", convert_string(repo_dto.name), row["scm_pr_id"])
                pr_detail = await self.bitbucket_client.get_pr_details()
                if pr_detail["state"] == "MERGED" or pr_detail["state"] == "DECLINED":
                    pr_closed_at = convert_to_datetime(pr_detail["updated_on"])
                    await PRService.db_update(
                        payload={"scm_close_time": pr_closed_at, "pr_state": pr_detail["state"]},
                        filters={"id": row["id"]},
                    )
                    logger.info(f"Marked data to merge / decline state for PR row - {row['id']}")
                else:
                    await PRService.db_update(
                        payload={"pr_state": pr_detail["state"]},
                        filters={"id": row["id"]},
                    )
                    logger.info(f"Marked data to open state for PR row - {row['id']}")

    async def backfill_pr_approval_time(self, query_params):
        """
        Backfill pull request data based on the given query parameters.

        Args:
            query_params: The query parameters containing start and end date for data retrieval.
        """
        pr_rows = await PRService.get_bulk_prs_by_filter(query_params)
        for row in pr_rows:
            repo_dto = await RepoService.db_get({"id": row["repo_id"]})
            self.bitbucket_client = BitbucketRepoClient("tata1mg", convert_string(repo_dto.name), row["scm_pr_id"])
            pr_detail = await self.bitbucket_client.get_pr_details()
            pr_approval_time = get_approval_time_from_participants_bitbucket(pr_detail.get("participants", []))
            if pr_approval_time:
                await PRService.db_update(
                    payload={"scm_approval_time": convert_to_datetime(pr_approval_time)},
                    filters={"id": row["id"]},
                )
                logger.info(f"PR approval time updated for - {row['id']}")
            else:
                logger.info(f"PR approval time not updated as PR is not approved - {row['id']}")
