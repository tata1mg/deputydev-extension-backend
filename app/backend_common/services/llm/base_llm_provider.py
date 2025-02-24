from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from torpedo import CONFIG

from app.backend_common.models.dto.message_thread_dto import (
    LLModels,
    ToolUseResponseMessageData,
)
from app.backend_common.services.llm.dataclasses.main import (
    ConversationTool,
    ConversationTurn,
    PromptCacheConfig,
    UnparsedLLMCallResponse,
    UserAndSystemMessages,
)


class BaseLLMProvider(ABC):
    """Abstract LLM interface"""

    def __init__(self, llm_type):
        self.llm_type = llm_type

    @abstractmethod
    def build_llm_payload(
        self,
        prompt: Optional[UserAndSystemMessages] = None,
        tool_use_response: Optional[ToolUseResponseMessageData] = None,
        previous_responses: List[ConversationTurn] = [],
        tools: Optional[List[ConversationTool]] = None,
        cache_config: PromptCacheConfig = PromptCacheConfig(tools=False, system_message=False, conversation=False),
    ) -> Dict[str, Any]:
        """
        Formats the conversation as required by the specific LLM.
        Args:
            prompt (Dict[str, str]): A prompt object containing system and user messages.
        Returns:
            Any: Formatted conversation ready to be sent to the LLM.
        """
        raise NotImplementedError("Must implement format_conversation in subclass")

    def _get_model_config(self, model: LLModels) -> Dict[str, Any]:
        return CONFIG.config.get("LLM_MODELS").get(model.value)

    async def call_service_client(
        self, llm_payload: Dict[str, Any], model: LLModels, stream: bool = False, response_type: Optional[str] = None
    ) -> UnparsedLLMCallResponse:
        """
        Calls the LLM service client.
        Args:
            llm_payload (Dict[str, Any]): The formatted conversation to send to the LLM.
            model (LLModels): The LLM model to use.
            stream (bool): If True, stream the response.
            response_type (str): The type of response expected ("text", "json").
        Returns:
            Any: The raw response from the LLM.
        """
        raise NotImplementedError()
