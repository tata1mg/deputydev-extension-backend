from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

from app.backend_common.services.llm.dataclasses.main import ConversationTool, LLMToolChoice
from app.backend_common.services.llm.dataclasses.unified_conversation_turn import UnifiedConversationTurn
from app.backend_common.services.llm.prompts.base_prompt import BasePrompt


class LLMHandlerInputs(BaseModel):
    # user_message: str  # noqa: ERA001
    # system_message: Optional[str] = None  # noqa: ERA001
    tools: Optional[List[ConversationTool]] = None
    tool_choice: LLMToolChoice = LLMToolChoice.AUTO
    prompt: Type[BasePrompt]
    messages: List[UnifiedConversationTurn]

    # TODO: Move to user and system messages
    extra_prompt_vars: Dict[str, Any] = {}
