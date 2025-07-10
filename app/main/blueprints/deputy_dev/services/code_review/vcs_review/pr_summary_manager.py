import re
from typing import Any, Dict, List, Tuple, Optional
from deputydev_core.utils.app_logger import AppLogger

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
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.base_pr_review_manager import (
    BasePRReviewManager,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.multi_agent_pr_review_manager import (
    MultiAgentPRReviewManager,
)
from app.main.blueprints.deputy_dev.services.setting.setting_service import (
    SettingService,
)
from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import (
    AgentAndInitParams,
    AgentTypes,
    AgentRunResult,
)
from app.main.blueprints.deputy_dev.services.comment.base_comment import BaseComment
from app.main.blueprints.deputy_dev.models.chat_request import ChatRequest


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
        valid_agents_and_init_params = cls.get_valid_agents_and_init_params_for_review()

        non_error_results, is_large_pr = await review_manager.get_code_review_comments(valid_agents_and_init_params)


        await cls.post_process_review_results(
            agent_results=non_error_results, is_large_pr=is_large_pr, comment_service=comment_service, chat_request=chat_request
        )

    @classmethod
    async def post_process_review_results(
            cls,
            agent_results: List[AgentRunResult],
            is_large_pr: bool,
            comment_service: BaseComment,
            chat_request: ChatRequest,
    ) -> Tuple[Optional[List[Dict[str, Any]]], Dict[str, Any], Dict[str, Any], bool]:
        """Post-process agent results to generate final comments and metadata.

        Args:
            agent_results: List of agent run results
            is_large_pr: Whether this is a large PR
            comment_service: Comment service
            chat_request: Chat Request payload

        Returns:
            Tuple of (comments, tokens_data, meta_info_to_save, is_large_pr)
        """
        if is_large_pr:
            await comment_service.create_comment_on_parent("PR is too large for summarization", chat_request.comment.id)
            return

        agent_results_dict: Dict[str, AgentRunResult] = {}

        for agent_result in agent_results:
            if agent_result.agent_result is not None:
                if agent_result.agent_type != AgentTypes.PR_SUMMARY:
                    cls._update_bucket_name(agent_result)
                agent_results_dict[agent_result.agent_name] = agent_result

        pr_summary_result = agent_results_dict.pop(AgentTypes.PR_SUMMARY.value, None)
        pr_summary = pr_summary_result.agent_result if pr_summary_result else None

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

    @classmethod
    def get_valid_agents_and_init_params_for_review(
            cls,
    ) -> List[AgentAndInitParams]:
        valid_agents: List[AgentAndInitParams] = []

        # add predefined and custom code commenter agents
        code_review_agent_rules = SettingService.helper.global_code_review_agent_rules()
        if code_review_agent_rules.get("enable"):
            agent_settings = SettingService.helper.agents_settings()
            for agent_name, agent_setting in agent_settings.items():
                if agent_setting["enable"]:
                    if agent_setting["is_custom_agent"]:
                        valid_agents.append(
                            AgentAndInitParams(
                                agent_type=AgentTypes.CUSTOM_COMMENTER_AGENT,
                                init_params={"custom_commenter_name": agent_name},
                            )
                        )
                    else:
                        try:
                            agent_name = AgentTypes(agent_name)
                            valid_agents.append(AgentAndInitParams(agent_type=agent_name))
                        except ValueError:
                            AppLogger.log_warn(f"Invalid agent name: {agent_name}")

        # add code summarization agent
        summary_agent_setting = SettingService.helper.summary_agent_setting()
        if summary_agent_setting.get("enable"):
            valid_agents.append(AgentAndInitParams(agent_type=AgentTypes.PR_SUMMARY))

        return valid_agents

    @staticmethod
    def _update_bucket_name(agent_result: AgentRunResult):
        """Update bucket names for agent result comments."""
        comments = agent_result.agent_result["comments"]
        for comment in comments:
            display_name = agent_result.display_name
            comment.bucket = "_".join(display_name.upper().split())
