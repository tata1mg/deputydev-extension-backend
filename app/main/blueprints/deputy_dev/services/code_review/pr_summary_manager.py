import re

from sanic.log import logger
from torpedo import CONFIG

from app.backend_common.repository.repo.repo_service import RepoService
from app.backend_common.services.llm.providers.openai_llm import OpenaiLLM
from app.backend_common.services.workspace.workspace_service import WorkspaceService
from app.common.utils.context_vars import set_context_values
from app.main.blueprints.deputy_dev.models.chat_request import ChatRequest
from app.main.blueprints.deputy_dev.services.code_review.agent_services.openai.openai_summary_agent import (
    OpenAIPRSummaryAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.base_review_manager import (
    BaseReviewManager,
)
from app.main.blueprints.deputy_dev.services.code_review.context.context_service import (
    ContextService,
)
from app.main.blueprints.deputy_dev.services.setting.setting_service import (
    SettingService,
)


class PRSummaryManager(BaseReviewManager):
    def __init__(self):
        self.llm = OpenaiLLM()

    async def generate_and_post_summary(self, chat_request: ChatRequest) -> None:
        """Generate PR summary and post it as a reply."""
        try:
            service_data = self.prepare_service_data_from_chat_request(chat_request)
            repo_service, pr_service, comment_service = await self.initialise_services(service_data)
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
            custom_prompt = self.parse_summary_prompt(chat_request.comment.raw)
            if custom_prompt:
                setting["pr_summary"]["custom_prompt"] = custom_prompt
                set_context_values(setting=setting)

            await self._process_summary(repo_service, pr_service, comment_service, chat_request)
        except Exception as e:
            logger.error(f"Error generating PR summary: {e}")
            raise

    async def _process_summary(self, repo_service, pr_service, comment_service, chat_request):
        """Process PR summary generation and posting."""
        context_service = ContextService(repo_service, pr_service)
        summary_agent = OpenAIPRSummaryAgent(context_service, is_reflection_enabled=False)

        prompt_data = await summary_agent.get_without_reflection_prompt()

        if prompt_data["exceeds_tokens"]:
            await comment_service.create_comment_on_parent(
                "PR is too large for summarization", chat_request.comment.id
            )
            return

        messages = self.llm.build_llm_message(
            {"system_message": prompt_data["system_message"], "user_message": prompt_data["user_message"]}
        )

        response = await self.llm.call_service_client(
            messages=messages,
            model=CONFIG.config.get("LLM_MODELS").get(summary_agent.model).get("NAME"),
            response_type="text",
        )

        summary, _, _ = await self.llm.parse_response(response)

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
    def prepare_service_data_from_chat_request(chat_request: ChatRequest) -> dict:
        return {
            "vcs_type": chat_request.repo.vcs_type,
            "repo_name": chat_request.repo.repo_name,
            "pr_id": chat_request.repo.pr_id,
            "workspace": chat_request.repo.workspace,
            "workspace_id": chat_request.repo.workspace_id,
            "repo_id": chat_request.repo.repo_id,
            "workspace_slug": chat_request.repo.workspace_slug,
        }
