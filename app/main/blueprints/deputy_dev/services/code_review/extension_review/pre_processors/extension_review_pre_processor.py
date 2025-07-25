from app.backend_common.repository.chat_attachments.repository import ChatAttachmentsRepository
from app.backend_common.repository.repo.repository import RepoRepository
from app.backend_common.caches.extension_review_cache import ExtensionReviewCache
from app.backend_common.service_clients.aws.services.s3 import AWSS3ServiceClient
from app.backend_common.services.chat_file_upload.chat_file_upload import ChatFileUpload
from app.backend_common.services.llm.dataclasses.main import ChatAttachmentDataWithObjectBytes
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
from app.main.blueprints.deputy_dev.services.code_review.extension_review.pre_processors.test_diff import diff
from app.main.blueprints.deputy_dev.services.code_review.extension_review.dataclass.main import ReviewRequest
from app.backend_common.models.dao.postgres.user_teams import UserTeams
from app.main.blueprints.deputy_dev.services.code_review.extension_review.dataclass.main import GetRepoIdRequest

class ExtensionReviewPreProcessor:
    def __init__(self):
        self.extension_repo_dto = None
        self.session_id = None
        self.review_dto = None
        self.review_status = ExtensionReviewStatusTypes.IN_PROGRESS.value
        self.is_valid = True

    async def _get_attachment_data_and_metadata(
        self,
        attachment_id: int,
    ) -> ChatAttachmentDataWithObjectBytes:
        """
        Get attachment data and metadata
        """

        attachment_data = await ChatAttachmentsRepository.get_attachment_by_id(attachment_id=attachment_id)
        if not attachment_data:
            raise ValueError(f"Attachment with id {attachment_id} not found")

        s3_key = attachment_data.s3_key
        object_bytes = await ChatFileUpload.get_file_data_by_s3_key(s3_key=s3_key)

        return ChatAttachmentDataWithObjectBytes(attachment_metadata=attachment_data, object_bytes=object_bytes)
    
    async def get_repo_id(self, request : GetRepoIdRequest, user_team_id: int):
        user_team = await UserTeamRepository.db_get(filters={"id": user_team_id}, fetch_one=True)
        if not user_team:
            raise ValueError(f"User team with id {user_team_id} not found")
        
        repo_dto = await RepoRepository.find_or_create_extension_repo(
            repo_name=request.repo_name,
             repo_origin=request.origin_url,
             team_id=user_team.team_id
        )
        return repo_dto

        
    async def pre_process_pr(self, data: dict, user_team_id: int):
        review_request = ReviewRequest(**data)

        # review_diff = self._get_attachment_data_and_metadata(attachment_id)

        combined_diff = ""
        for file in review_request.file_wise_diff:
            combined_diff += file.diff
        
        review_diff = combined_diff

        reviewed_files = [file.file_path for file in review_request.file_wise_diff]

        diff_handler = ExtensionDiffHandler(review_diff)
        loc = diff_handler.get_diff_loc()
        token_count = diff_handler.get_diff_token_count()

        user_team = await UserTeamRepository.db_get(filters={"id": user_team_id}, fetch_one=True)

        self.extension_repo_dto = await RepoRepository.find_or_create_extension_repo(
            repo_name=review_request.repo_name,
             repo_origin=review_request.origin_url,
             team_id=user_team.team_id
        )

        session = await MessageSessionsRepository.create_message_session(
            message_session_data=MessageSessionData(
                user_team_id=user_team_id,
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
            diff_s3_url="testing",
            session_id=self.session_id,
            meta_info={"tokens": token_count},
            source_branch=review_request.source_branch,
            target_branch=review_request.target_branch,
            source_commit=review_request.source_commit,
            target_commit=review_request.target_commit,
        )
        self.review_dto = await ExtensionReviewsRepository.db_insert(review_dto)

        if self.is_valid:
            a = await ExtensionReviewCache.set(key=str(self.review_dto.id), value=review_diff)

        return {
            "review_id": self.review_dto.id,
            "session_id": self.session_id,
            "repo_id": self.extension_repo_dto.id,
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
