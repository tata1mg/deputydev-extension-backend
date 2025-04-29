from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.prompts.base_prompt import BasePrompt


class BaseGemini2Point5ProPrompt(BasePrompt):
    model_name = LLModels.GEMINI_2_POINT_5_PRO
