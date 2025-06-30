from app.main.blueprints.deputy_dev.services.code_review.pre_processors.base_review_pre_processor import BaseReviewPreProcessor
from app.backend_common.repository.repo.repository import RepoRepository
from app.backend_common.caches.extension_review_cache import ExtensionReviewCache
from app.backend_common.service_clients.aws.services.s3 import AWSS3ServiceClient
from torpedo import CONFIG

class ExtensionReviewPreProcessor(BaseReviewPreProcessor):
    def __init__(self):
        super().__init__()
        self.extension_repo_dto = None
        self.setting = None

    async def pre_process_pr(self, data: dict):
        """
        1. Find or create extension repo.
        2. Fetch setting
        3. Run validations
        4. If valid, store diff in cache.
        5. Fetch agents
        6. Return agent list.
        """
        repo_name = data.get("repo_name")
        diff_s3_url = data.get("diff_s3_url")
        s3_bucket = CONFIG.config["S3"]["EXTENSION_REVIEW_DIFF_BUCKET"]
        s3_region = CONFIG.config["S3"]["EXTENSION_REVIEW_DIFF_REGION"]
        s3_client = AWSS3ServiceClient(bucket_name=s3_bucket, region_name=s3_region)
        review_diff_bytes = await s3_client.get_object(diff_s3_url)
        review_diff = review_diff_bytes.decode("utf-8")
        user_team_id = data.get("user_team_id")

        self.extension_repo_dto = await RepoRepository.find_or_create(
            user_team_id=user_team_id,
            repo_name=repo_name,
            repo_path=repo_name,  # repo path or name
        )

        self.setting = await self.fetch_setting()

        await self.run_validation(review_diff)

        if self.is_valid:
            await ExtensionReviewCache.set(
                key=self.extension_repo_dto.repo_id,
                value=review_diff
            )

        agent_list = await self.fetch_agents(self.extension_repo_dto.repo_id)

        return agent_list

    async def fetch_setting(self):
        """
        Fetch settings for the extension repo.
        """
        # TODO: Implement fetching settings logic
        pass

    async def run_validation(self, review_diff: str):
        """
        Run validations on the review diff, token count, based on setting, MAX_DIFF_TOKEN_LIMIT.
        """
        # TODO: Implement validation logic
        pass

    async def fetch_agents(self, repo_id: str):
        """
        Fetch agents for the given repo_id.
        """
        # TODO: Implement agent fetching logic
        pass