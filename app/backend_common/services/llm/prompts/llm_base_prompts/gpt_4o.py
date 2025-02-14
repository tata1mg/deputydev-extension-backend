from app.backend_common.services.llm.dataclasses.main import LLModels
from app.backend_common.services.llm.prompts.base_prompt import BasePrompt


class BaseGPT4OPrompt(BasePrompt):
    model_name = LLModels.GPT_4O
