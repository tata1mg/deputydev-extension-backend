from app.common.constants.constants import LLModels
from app.backend_common.services.llm.base_prompt import BasePrompt


class BaseGPT4OPrompt(BasePrompt):
    model_name = LLModels.GPT_4O
