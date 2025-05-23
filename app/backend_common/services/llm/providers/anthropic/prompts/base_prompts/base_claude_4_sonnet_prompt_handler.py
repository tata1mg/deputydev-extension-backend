from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.providers.anthropic.prompts.base_prompts.base_claude_prompt_handler import (
    BaseClaudePromptHandler,
)


class BaseClaude4SonnetPromptHandler(BaseClaudePromptHandler):
    model_name = LLModels.CLAUDE_4_SONNET
