from sanic.log import logger
from app.common.service_clients.bitbucket.bitbucket_repo_client import (
    BitbucketRepoClient,
)
from app.common.utils.app_utils import convert_string
from app.main.blueprints.deputy_dev.services.experiment.experiment_service import ExperimentService
from app.main.blueprints.deputy_dev.services.pr.pr_service import PRService
from app.main.blueprints.deputy_dev.services.repo.repo_service import RepoService
from app.main.blueprints.deputy_dev.services.stats_collection.merge_metrics_manager import MergeMetricsManager


class PRDataManager:
    def __init__(self):
        self.bitbucket_client = None

    async def update_pr_data(self, query_params):
        pr_rows = await PRService.get_bulk_prs_by_filter(query_params)
        for pr in pr_rows:
            scm_pr_id = pr["scm_pr_id"]
            repo_id = pr["repo_id"]
            repo_dto = await RepoService.db_get({"id": repo_id})
            experiment_dto = await ExperimentService.db_get({"pr_id": pr["id"]})
            if repo_dto and experiment_dto:
                self.bitbucket_client = BitbucketRepoClient("tata1mg", convert_string(repo_dto.name), scm_pr_id)
                all_comments = await self.bitbucket_client.get_pr_comments()
                llm_comment_count, human_comment_count = MergeMetricsManager.count_bot_and_human_comments(
                    all_comments
                )
                logger.info(f"PR info - {pr}")
                # Ideally we should be doing this update in batches, but since we have less thand 450 data in experiment
                # table as of the time of adding this comment, we can do this one by one for now.
                await ExperimentService.db_update(
                    payload={"human_comment_count": human_comment_count, "llm_comment_count": llm_comment_count},
                    filters={"pr_id": pr["id"]},
                )
