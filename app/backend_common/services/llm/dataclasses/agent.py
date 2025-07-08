from app.backend_common.services.llm.dataclasses.main import ConversationTool, LLMToolChoice
from app.backend_common.services.llm.prompts.base_prompt import BasePrompt


from pydantic import BaseModel


from typing import List, Optional, Type


class LLMHandlerInputs(BaseModel):
    # user_message: str  # noqa: ERA001
    # system_message: Optional[str] = None  # noqa: ERA001
    tools: Optional[List[ConversationTool]] = None
    tool_choice: LLMToolChoice = LLMToolChoice.AUTO
    prompt: Type[BasePrompt]
    previous_messages: List[int] = []