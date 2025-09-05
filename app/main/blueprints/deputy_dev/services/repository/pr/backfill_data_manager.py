from typing import Any, Dict

from sanic.log import logger

from app.backend_common.models.dto.pr.bitbucket_pr import BitbucketPrModel
from app.backend_common.models.dto.pr.github_pr import GitHubPrModel
from app.backend_common.repository.repo.repository import RepoRepository
from app.backend_common.service_clients.bitbucket import BitbucketRepoClient
from app.backend_common.service_clients.github.github_repo_client import (
    GithubRepoClient,
)
from app.backend_common.utils.app_utils import convert_to_datetime, name_to_slug
from app.main.blueprints.deputy_dev.constants.constants import PrStatusTypes
from app.main.blueprints.deputy_dev.services.experiment.experiment_service import (
    ExperimentService,
)
from app.main.blueprints.deputy_dev.services.repository.pr.pr_service import PRService
from app.main.blueprints.deputy_dev.utils import (
    count_bot_and_human_comments_bitbucket,
    get_approval_time_from_participants_bitbucket,
    get_vcs_auth_handler,
)


class BackfillManager:
    def __init__(self) -> None:
        self.bitbucket_client = None

    async def backfill_comments_count_in_experiments_table(self, query_params: Dict[str, Any]) -> None:
        pr_rows = await PRService.get_bulk_prs_by_filter(query_params)
        for pr in pr_rows:
            scm_pr_id = pr["scm_pr_id"]
            repo_id = pr["repo_id"]
            repo_dto = await RepoRepository.db_get({"id": repo_id}, fetch_one=True)
            experiment_dto = await ExperimentService.db_get({"pr_id": pr["id"]})
            if repo_dto and experiment_dto:
                self.bitbucket_client = BitbucketRepoClient("tata1mg", name_to_slug(repo_dto.name), scm_pr_id)
                all_comments = await self.bitbucket_client.get_pr_comments()
                llm_comment_count, human_comment_count = count_bot_and_human_comments_bitbucket(all_comments)
                # Ideally we should be doing this update in batches, but since we have less thand 450 data in experiment
                # table as of the time of adding this comment, we can do this one by one for now.
                await ExperimentService.db_update(
                    payload={"human_comment_count": human_comment_count, "llm_comment_count": llm_comment_count},
                    filters={"pr_id": pr["id"]},
                )
                logger.info(f"Backfilling of comment counts completed for - {pr['id']}")

    async def backfill_experiment_data(self, query_params: Dict[str, Any]) -> None:
        """
        Backfill experiment and pull request data based on the given query parameters.

        Args:
            query_params: The query parameters containing start and end date for data retrieval.
        """
        exp_rows = await ExperimentService.get_data_in_range(query_params.get("start"), query_params.get("end"))
        for row in exp_rows:
            repo_dto = await RepoRepository.db_get({"id": row.repo_id}, fetch_one=True)
            pr_dto = await PRService.db_get({"id": row.pr_id})
            if repo_dto and pr_dto:
                # We will be fetching the PR details for every row in the table to backfill pr_state for each row
                self.bitbucket_client = BitbucketRepoClient("tata1mg", name_to_slug(repo_dto.name), pr_dto.scm_pr_id)
                pr_detail = await self.bitbucket_client.get_pr_details()
                if row.scm_close_time is None and row.close_time_in_sec is None:
                    if pr_detail["state"] == "MERGED" or pr_detail["state"] == "DECLINED":
                        all_comments = await self.bitbucket_client.get_pr_comments()
                        llm_comment_count, human_comment_count = count_bot_and_human_comments_bitbucket(all_comments)

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

    async def backfill_pullrequests_data(self, query_params: Dict[str, Any]) -> None:
        """
        Backfill pull request data based on the given query parameters.

        Args:
            query_params: The query parameters containing start and end date for data retrieval.
        """
        pr_rows = await PRService.get_bulk_prs_by_filter(query_params)

        for row in pr_rows:
            try:
                repo_dto = (await RepoRepository.db_get({"id": row["repo_id"]}))[0]
                if repo_dto.team_id == 1 and repo_dto.scm == "bitbucket":
                    onemg_workspace_id = "{eac19072-5edc-44b0-a9fc-206356051d1e}"
                    auth_handler = await get_vcs_auth_handler(onemg_workspace_id, "bitbucket")
                    self.client = BitbucketRepoClient(
                        "tata1mg", name_to_slug(repo_dto.name), int(row["scm_pr_id"]), auth_handler
                    )
                    pr_detail = await self.client.get_pr_details()
                    pr_model = BitbucketPrModel(pr_detail)
                elif repo_dto.team_id == 1 and repo_dto.scm == "github":
                    onemg_workspace_id = "142996019"
                    auth_handler = await get_vcs_auth_handler(onemg_workspace_id, "github")
                    self.client = GithubRepoClient(
                        workspace_slug="tata1mg",
                        repo=name_to_slug(repo_dto.name),
                        pr_id=int(row["scm_pr_id"]),
                        auth_handler=auth_handler,
                    )
                    pr_detail = await self.client.get_pr_details()
                    pr_model = GitHubPrModel(await pr_detail.json())
                else:
                    traya_workspace_id = "129746479"
                    auth_handler = await get_vcs_auth_handler(traya_workspace_id, "github")
                    self.client = GithubRepoClient(
                        workspace_slug="trayalabs1",
                        repo=name_to_slug(repo_dto.name),
                        pr_id=int(row["scm_pr_id"]),
                        auth_handler=auth_handler,
                    )
                    pr_detail = await self.client.get_pr_details()
                    pr_model = GitHubPrModel(await pr_detail.json())
                if pr_model.scm_state() == "MERGED" or pr_model.scm_state() == "DECLINED":
                    pr_closed_at = convert_to_datetime(pr_model.scm_updation_time())
                    await PRService.db_update(
                        payload={"scm_close_time": pr_closed_at, "pr_state": pr_model.scm_state()},
                        filters={"id": row["id"]},
                    )
                    logger.info(f"Marked data to merge / decline state for PR row - {row['id']}")
            except Exception as error:  # noqa: BLE001
                logger.info(f"Error occured for {row['id']} error: {error} pr_details: {pr_detail}")

    async def backfill_pr_approval_time(self, query_params: Dict[str, Any]) -> None:
        """
        Backfill pull request data based on the given query parameters.

        Args:
            query_params: The query parameters containing start and end date for data retrieval.
        """
        pr_rows = await PRService.get_bulk_prs_by_filter(query_params)
        for row in pr_rows:
            repo_dto = await RepoRepository.db_get({"id": row["repo_id"]}, fetch_one=True)
            self.bitbucket_client = BitbucketRepoClient("tata1mg", name_to_slug(repo_dto.name), row["scm_pr_id"])
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
