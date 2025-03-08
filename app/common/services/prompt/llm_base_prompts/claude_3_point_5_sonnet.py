from app.backend_common.constants.constants import LLModels
from app.common.services.prompt.base_prompt import BasePrompt


class BaseClaude3Point5SonnetPrompt(BasePrompt):
    model_name = LLModels.CLAUDE_3_POINT_5_SONNET
