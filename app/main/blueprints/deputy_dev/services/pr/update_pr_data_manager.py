from sanic.log import logger

from app.common.service_clients.bitbucket.bitbucket_repo_client import (
    BitbucketRepoClient,
)
from app.common.utils.app_utils import get_token_count
from app.main.blueprints.deputy_dev.services.pr.pr_service import PRService
from app.main.blueprints.deputy_dev.services.repo.repo_service import RepoService
from app.main.blueprints.deputy_dev.utils import ignore_files


class PRDataManager:
    def __init__(self):
        self.bitbucket_client = BitbucketRepoClient("", "", "")

    async def update_pr_data(self, query_params):
        pr_rows = await PRService.get_bulk_prs_by_filter(query_params)
        count = 1
        for pr in pr_rows:
            scm_pr_id = pr["scm_pr_id"]
            repo_id = pr["repo_id"]
            repo_dto = await RepoService.db_get({"id": repo_id})
            if repo_dto:
                loc_count = await self.bitbucket_client.fetch_diffstat(repo_dto.name, scm_pr_id)
                pr_diff = await self.bitbucket_client.get_pr_diff_v1(repo_dto.name, scm_pr_id)
                pr_diff = ignore_files(pr_diff[0])
                pr_diff_token_count = get_token_count(pr_diff)
                await PRService.update_meta_info(pr["id"], loc_count, pr_diff_token_count)
                logger.info("Data updated for ID {}. Count: {}".format(pr["id"], count))
                count += 1
