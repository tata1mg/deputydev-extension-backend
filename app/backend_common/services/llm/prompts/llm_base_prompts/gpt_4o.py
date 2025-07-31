from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.prompts.base_prompt import BasePrompt


class BaseGPT4POINT1Prompt(BasePrompt):
    model_name = LLModels.GPT_4_POINT_1
