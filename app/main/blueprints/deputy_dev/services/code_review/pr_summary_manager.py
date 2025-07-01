import re
from typing import Any, Dict

from deputydev_core.utils.constants.enums import Clients
from deputydev_core.utils.context_vars import set_context_values

from app.backend_common.models.dto.message_sessions_dto import MessageSessionData
from app.backend_common.models.dto.user_team_dto import UserTeamDTO
from app.backend_common.repository.message_sessions.repository import (
    MessageSessionsRepository,
)
from app.backend_common.repository.repo.repository import RepoRepository
from app.backend_common.repository.user_teams.user_team_repository import (
    UserTeamRepository,
)
from app.main.blueprints.deputy_dev.constants.constants import (
    PR_REVIEW_POST_AFFIRMATION_MESSAGES,
    FeatureFlows,
    PrStatusTypes,
)
from app.main.blueprints.deputy_dev.helpers.pr_diff_handler import PRDiffHandler
from app.main.blueprints.deputy_dev.models.chat_request import ChatRequest
from app.main.blueprints.deputy_dev.services.code_review.agents.dataclasses.main import (
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.base_pr_review_manager import (
    BasePRReviewManager,
)
from app.main.blueprints.deputy_dev.services.code_review.multi_agent_pr_review_manager import (
    MultiAgentPRReviewManager,
)
from app.main.blueprints.deputy_dev.services.setting.setting_service import (
    SettingService,
)


class PRSummaryManager(BasePRReviewManager):
    @classmethod
    async def generate_and_post_summary(cls, chat_request: ChatRequest) -> None:
        """Generate PR summary and post it as a reply."""
        set_context_values(feature_flow=FeatureFlows.INCREMENTAL_SUMMARY.value)
        service_data = cls.extract_service_initializing_metadata(chat_request)
        repo_service, pr_service, comment_service = await cls.initialise_services(service_data)

        # This creates repo entry in db if not exist.
        repo_dto = await RepoRepository.find_or_create_with_workspace_id(
            scm_workspace_id=chat_request.repo.workspace_id, pr_model=pr_service.pr_model()
        )
        set_context_values(team_id=repo_dto.team_id)
        team_id = repo_dto.team_id

        setting = await SettingService(repo_service, team_id).build()
        if not setting["pr_summary"]["enable"]:
            await comment_service.process_chat_comment(
                comment=PR_REVIEW_POST_AFFIRMATION_MESSAGES[PrStatusTypes.SUMMARY_DISABLED.value],
                chat_request=chat_request,
            )

        custom_prompt = cls.parse_summary_prompt(chat_request.comment.raw)
        if custom_prompt:
            setting["pr_summary"]["custom_prompt"] = custom_prompt
            set_context_values(setting=setting)

        await cls._process_summary(repo_service, pr_service, comment_service, chat_request, team_id)

    @classmethod
    async def _process_summary(cls, repo_service, pr_service, comment_service, chat_request, team_id):
        """Process PR summary generation and posting."""
        pr_diff_handler = PRDiffHandler(pr_service)

        user_team_dto: UserTeamDTO = await UserTeamRepository.db_get(
            {"team_id": team_id, "is_owner": True}, fetch_one=True
        )
        if not user_team_dto or not user_team_dto.id:
            raise Exception("Owner not found for the team")
        session = await MessageSessionsRepository.create_message_session(
            message_session_data=MessageSessionData(
                user_team_id=user_team_dto.id, client=Clients.BACKEND, client_version="1.0.0", session_type="PR_SUMMARY"
            )
        )

        review_manager = MultiAgentPRReviewManager(
            repo_service=repo_service,
            pr_service=pr_service,
            pr_diff_handler=pr_diff_handler,
            eligible_agents=[AgentTypes.PR_SUMMARY],
            session_id=session.id,
        )

        # Get summary using MultiAgentPRReviewManager
        _, pr_summary, agents_tokens, _, is_large_pr = await review_manager.get_code_review_comments()
        if is_large_pr:
            await comment_service.create_comment_on_parent("PR is too large for summarization", chat_request.comment.id)
            return

        await comment_service.process_chat_comment(
            comment=pr_summary,
            chat_request=chat_request,
        )

    @staticmethod
    def parse_summary_prompt(comment: str):
        """
        Parse summary command from comment.
        Returns None if comment doesn't start with #summary.
        """
        summary_regx = r"^#summary(?:\s+-prompt\s+(.+))?$"
        if not comment:
            return None

        match = re.match(summary_regx, comment.strip())
        if not match:
            return None

        return match.group(1)

    @staticmethod
    def extract_service_initializing_metadata(chat_request: ChatRequest) -> Dict[str, Any]:
        return {
            "vcs_type": chat_request.repo.vcs_type,
            "repo_name": chat_request.repo.repo_name,
            "pr_id": chat_request.repo.pr_id,
            "workspace": chat_request.repo.workspace,
            "workspace_id": chat_request.repo.workspace_id,
            "repo_id": chat_request.repo.repo_id,
            "workspace_slug": chat_request.repo.workspace_slug,
        }
