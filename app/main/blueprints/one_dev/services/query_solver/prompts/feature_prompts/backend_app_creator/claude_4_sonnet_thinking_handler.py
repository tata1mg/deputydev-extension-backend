from app.backend_common.models.dto.message_thread_dto import LLModels
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.backend_app_creator.claude_4_sonnet_handler import (
    Claude4BackendAppCreatorPromptHandler,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.backend_app_creator.prompts.claude.claude_4_thinking_backend_app_creator_prompt import (
    Claude4ThinkingBackendAppCreatorPrompt,
)


class Claude4ThinkingBackendAppCreatorPromptHandler(Claude4BackendAppCreatorPromptHandler):
    model_name = LLModels.CLAUDE_4_SONNET_THINKING
    prompt_class = Claude4ThinkingBackendAppCreatorPrompt
