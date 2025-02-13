from app.backend_common.services.llm.base_prompt import BasePrompt
from app.common.constants.constants import LLModels


class BaseGPT4OPrompt(BasePrompt):
    model_name = LLModels.GPT_4O
