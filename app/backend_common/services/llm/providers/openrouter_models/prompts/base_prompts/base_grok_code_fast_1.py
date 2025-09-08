from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.providers.openrouter_models.prompts.base_prompts.base_openrouter_model_prompt_handler import (
    BaseOpenrouterModelPromptHandler,
)


class BaseGrokCodeFast1Prompt(BaseOpenrouterModelPromptHandler):
    model_name = LLModels.OPENROUTER_GROK_CODE_FAST_1
