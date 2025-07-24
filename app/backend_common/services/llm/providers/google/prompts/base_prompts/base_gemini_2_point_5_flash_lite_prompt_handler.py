from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.providers.google.prompts.base_prompts.base_gemini_prompt_handler import (
    BaseGeminiPromptHandler,
)


class BaseGemini2Point5FlashLitePromptHandler(BaseGeminiPromptHandler):
    model_name = LLModels.GEMINI_2_POINT_5_FLASH_LITE
