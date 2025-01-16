import re

from app.backend_common.repository.repo.repo_service import RepoService
from app.backend_common.services.llm.providers.openai_llm import OpenaiLLM
from app.backend_common.services.workspace.workspace_service import WorkspaceService
from app.common.utils.app_logger import AppLogger
from app.common.utils.context_vars import set_context_values
from app.main.blueprints.deputy_dev.helpers.pr_diff_handler import PRDiffHandler
from app.main.blueprints.deputy_dev.models.chat_request import ChatRequest
from app.main.blueprints.deputy_dev.services.code_review.agent_services.agent_factory import (
    AgentFactory,
)
from app.main.blueprints.deputy_dev.services.code_review.base_review_manager import (
    BasePRReviewManager,
)
from app.main.blueprints.deputy_dev.services.code_review.context.context_service import (
    ContextService,
)
from app.main.blueprints.deputy_dev.services.setting.setting_service import (
    SettingService,
)


class PRSummaryManager(BasePRReviewManager):
    llm = OpenaiLLM()

    @classmethod
    async def generate_and_post_summary(cls, chat_request: ChatRequest) -> None:
        """Generate PR summary and post it as a reply."""
        try:
            service_data = cls.extract_service_initializing_metadata(chat_request)
            repo_service, pr_service, comment_service = await cls.initialise_services(service_data)
            workspace_dto = await WorkspaceService.find(
                scm_workspace_id=chat_request.repo.workspace_id, scm=chat_request.repo.vcs_type
            )
            team_id = None
            if workspace_dto:
                set_context_values(team_id=workspace_dto.team_id)
                team_id = workspace_dto.team_id

            # This creates repo entry in db if not exist.
            await RepoService.find_or_create_with_workspace_id(
                scm_workspace_id=chat_request.repo.workspace_id, pr_model=pr_service.pr_model()
            )
            setting = await SettingService(repo_service, team_id).build()
            custom_prompt = cls.parse_summary_prompt(chat_request.comment.raw)
            if custom_prompt:
                setting["pr_summary"]["custom_prompt"] = custom_prompt
                set_context_values(setting=setting)

            await cls._process_summary(repo_service, pr_service, comment_service, chat_request)
        except Exception as e:
            AppLogger.log_error(f"Error generating PR summary: {e}")
            raise

    @classmethod
    async def _process_summary(cls, repo_service, pr_service, comment_service, chat_request):
        """Process PR summary generation and posting."""
        pr_diff_handler = PRDiffHandler(pr_service)
        context_service = ContextService(repo_service, pr_service, pr_diff_handler)

        agent_factory = AgentFactory(reflection_enabled=False, context_service=context_service)
        prompt_data = await agent_factory.build_pr_summary_prompt(
            reflection_stage=False, previous_review_comments={}, exclude_agents=[]
        )

        if prompt_data["exceeds_tokens"]:
            await comment_service.create_comment_on_parent("PR is too large for summarization", chat_request.comment.id)
            return

        messages = cls.llm.build_llm_message(
            {"system_message": prompt_data["system_message"], "user_message": prompt_data["user_message"]}
        )

        response = await cls.llm.call_service_client(
            messages=messages,
            model=prompt_data.get("model"),
            response_type="text",
        )

        summary, _, _ = await cls.llm.parse_response(response)

        await comment_service.process_chat_comment(
            comment=summary,
            chat_request=chat_request,
            reply_to_root=True,
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
    def extract_service_initializing_metadata(chat_request: ChatRequest) -> dict:
        return {
            "vcs_type": chat_request.repo.vcs_type,
            "repo_name": chat_request.repo.repo_name,
            "pr_id": chat_request.repo.pr_id,
            "workspace": chat_request.repo.workspace,
            "workspace_id": chat_request.repo.workspace_id,
            "repo_id": chat_request.repo.repo_id,
            "workspace_slug": chat_request.repo.workspace_slug,
        }
