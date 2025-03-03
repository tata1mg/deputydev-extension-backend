from app.backend_common.constants.constants import LLModels
from app.common.services.prompt.base_prompt import BasePrompt


class BaseGPT4OPrompt(BasePrompt):
    model_name = LLModels.GPT_4O
