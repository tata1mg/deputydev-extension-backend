from app.backend_common.services.llm.base_prompt import BasePrompt
from app.common.constants.constants import LLModels


class BaseClaude3Point5SonnetPrompt(BasePrompt):
    model_name = LLModels.CLAUDE_3_POINT_5_SONNET
