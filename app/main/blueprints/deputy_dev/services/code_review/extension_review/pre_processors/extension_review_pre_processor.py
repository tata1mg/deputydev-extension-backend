from app.backend_common.repository.repo.repository import RepoRepository
from app.backend_common.caches.extension_review_cache import ExtensionReviewCache
from app.backend_common.service_clients.aws.services.s3 import AWSS3ServiceClient
from torpedo import CONFIG
from app.backend_common.repository.user_teams.user_team_repository import (
    UserTeamRepository,
)
from app.backend_common.models.dto.message_sessions_dto import MessageSessionData
from app.backend_common.models.dto.user_team_dto import UserTeamDTO
from deputydev_core.utils.constants.enums import Clients
from app.backend_common.repository.message_sessions.repository import (
    MessageSessionsRepository,
)
from app.main.blueprints.deputy_dev.helpers.extension_diff_handler import ExtensionDiffHandler
from app.main.blueprints.deputy_dev.models.dto.extension_review_dto import ExtensionReviewDTO
from app.main.blueprints.deputy_dev.constants.constants import (
    MAX_PR_DIFF_TOKEN_LIMIT,
    PR_SIZE_TOO_BIG_MESSAGE,
    ExtensionReviewStatusTypes,
)
from app.backend_common.constants.constants import LARGE_PR_DIFF, PR_NOT_FOUND, PRStatus
from app.main.blueprints.deputy_dev.services.repository.extension_reviews.repository import ExtensionReviewsRepository


class ExtensionReviewPreProcessor:
    def __init__(self):
        self.extension_repo_dto = None
        self.session_id = None
        self.review_dto = None
        self.review_status = ExtensionReviewStatusTypes.IN_PROGRESS.value
        self.is_valid = True

    async def pre_process_pr(self, data: dict, user_team_id: int):

        repo_name = data.get("repo_name")
        repo_origin = data.get("repo_origin")
        diff_s3_url = data.get("diff_s3_url")
        source_branch = data.get("source_branch")
        target_branch = data.get("target_branch")

        s3_bucket = CONFIG.config["S3"]["EXTENSION_REVIEW_DIFF_BUCKET"]
        s3_region = CONFIG.config["S3"]["EXTENSION_REVIEW_DIFF_REGION"]
        s3_client = AWSS3ServiceClient(bucket_name=s3_bucket, region_name=s3_region)
        review_diff_bytes = await s3_client.get_object(diff_s3_url)
        review_diff = review_diff_bytes.decode("utf-8")

        diff_handler = ExtensionDiffHandler(review_diff)
        loc = diff_handler.get_diff_loc()
        reviewed_files = diff_handler.get_files()
        token_count = diff_handler.get_diff_token_count()

        self.extension_repo_dto = await RepoRepository.find_or_create_extension_repo(
            repo_name=repo_name, repo_origin=repo_origin, team_id=user_team_id
        )

        user_team_dto = await UserTeamRepository.db_get(
            {"team_id": self.extension_repo_dto.team_id, "is_owner": True}, fetch_one=True
        )
        if not user_team_dto or not user_team_dto.id:
            raise Exception("Owner not found for the team")

        session = await MessageSessionsRepository.create_message_session(
            message_session_data=MessageSessionData(
                user_team_id=user_team_dto.id,
                client=Clients.BACKEND,
                client_version="1.0.0",
                session_type="EXTENSION_REVIEW",
            )
        )
        self.session_id = session.id

        await self.run_validation(review_diff, token_count)

        review_dto = ExtensionReviewDTO(
            review_status=self.review_status,
            repo_id=self.extension_repo_dto.id,
            user_team_id=user_team_id,
            loc=loc,
            reviewed_files=reviewed_files,
            diff_s3_url=diff_s3_url,
            session_id=self.session_id,
            meta_info={"tokens": token_count}
        )
        self.review_dto = await ExtensionReviewsRepository.db_insert(review_dto)

        if self.is_valid:
            await ExtensionReviewCache.set(key=self.extension_repo_dto.repo_id, value=review_diff)

        return {
            "review_id": self.review_dto.id,
            "session_id": self.session_id,

        }


    async def run_validation(self, review_diff: str, token_count: int):
        """
        Run validations on the review diff, token count, based on setting, MAX_DIFF_TOKEN_LIMIT.
        """
        if not review_diff:
            self.is_valid = False
            self.review_status = ExtensionReviewStatusTypes.REJECTED_NO_DIFF.value
        elif token_count > MAX_PR_DIFF_TOKEN_LIMIT:
            self.is_valid = False
            self.review_status = ExtensionReviewStatusTypes.REJECTED_LARGE_SIZE.value

