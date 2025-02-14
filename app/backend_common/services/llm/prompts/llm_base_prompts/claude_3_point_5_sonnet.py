from app.backend_common.services.llm.dataclasses.main import LLModels
from app.backend_common.services.llm.prompts.base_prompt import BasePrompt


class BaseClaude3Point5SonnetPrompt(BasePrompt):
    model_name = LLModels.CLAUDE_3_POINT_5_SONNET
