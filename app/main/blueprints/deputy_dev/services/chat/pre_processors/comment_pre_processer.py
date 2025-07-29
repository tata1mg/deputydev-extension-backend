from enum import Enum

from app.backend_common.models.dto.pr.base_pr import BasePrModel
from app.backend_common.repository.repo.repository import RepoRepository
from app.backend_common.services.workspace.workspace_service import WorkspaceService
from app.main.blueprints.deputy_dev.constants.constants import (
    ChatTypes,
    FeedbackTypes,
    MessageTypes,
)
from app.main.blueprints.deputy_dev.models.chat_request import ChatRequest
from app.main.blueprints.deputy_dev.models.dto.feedback_dto import FeedbackDTO
from app.main.blueprints.deputy_dev.services.feedback.feedback_service import (
    FeedbackService,
)
from app.main.blueprints.deputy_dev.services.repository.pr.pr_service import PRService


class CommentPreprocessor(Enum):
    @classmethod
    async def process_chat(cls, chat_request: ChatRequest, pr_model: BasePrModel):
        message_type, feedback_type = cls.get_message_type(chat_request.comment.raw)
        if message_type == MessageTypes.FEEDBACK.value:
            await cls.save_feedback_info(feedback_type, chat_request, pr_model)
        return message_type

    @classmethod
    def get_message_type(cls, message: str):
        for _type in FeedbackTypes.list():
            if f"#{_type}" in message.lower():
                return MessageTypes.FEEDBACK.value, _type
        for _type in ChatTypes.list():
            if message.lower().startswith(f"#{_type}"):
                return MessageTypes.CHAT.value, _type
        return MessageTypes.UNKNOWN.value, None

    @classmethod
    async def save_feedback_info(cls, feedback_type, chat_request: ChatRequest, pr_model: BasePrModel):
        payload = await cls.extract_feedback_payload(feedback_type, chat_request, pr_model)
        result = await FeedbackService.db_insert(feedback_dto=FeedbackDTO(**payload))
        return result

    @classmethod
    async def extract_feedback_payload(cls, feedback_type, chat_request: ChatRequest, pr_model: BasePrModel):
        workspace_dto, repo_dto, pr_dto = None, None, None
        workspace_dto = await WorkspaceService.find(
            scm=pr_model.scm_type(),
            scm_workspace_id=pr_model.scm_workspace_id(),
        )
        if workspace_dto:
            repo_dto = await RepoRepository.db_get(
                filters=dict(scm_repo_id=pr_model.scm_repo_id(), workspace_id=workspace_dto.id), fetch_one=True
            )
            if repo_dto:
                pr_dto = await PRService.find(filters={"scm_pr_id": pr_model.scm_pr_id(), "repo_id": repo_dto.id})
        payload = {
            "feedback_type": feedback_type,
            "feedback": chat_request.comment.raw,
            "pr_id": pr_dto.id if pr_dto else None,
            "meta_info": {
                "commit_id": chat_request.repo.commit_id,
                "scm_comment_id": str(chat_request.comment.id),
                "scm_parent_comment_id": str(chat_request.comment.parent_comment_id),
                "scm_repo_name": pr_model.scm_repo_name(),
                "scm_repo_id": pr_model.scm_repo_id(),
            },
            "author_info": {
                "name": chat_request.author_info.name,
                "email": chat_request.author_info.email,
                "scm_author_id": chat_request.author_info.scm_author_id,
            },
            "scm": pr_model.scm_type(),
            "team_id": workspace_dto.team_id,
            "workspace_id": workspace_dto.id,
            "scm_pr_id": str(pr_model.scm_pr_id()),
            "repo_id": repo_dto.id if repo_dto else None,
        }
        return payload
