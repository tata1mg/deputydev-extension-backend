import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Literal, Optional

from deputydev_core.utils.config_manager import ConfigManager

from app.backend_common.models.dto.message_thread_dto import (
    LLModels,
    MessageThreadDTO,
    ToolUseResponseData,
)
from app.backend_common.services.llm.dataclasses.main import (
    ChatAttachmentDataWithObjectBytes,
    ConversationTool,
    PromptCacheConfig,
    UnparsedLLMCallResponse,
    UserAndSystemMessages,
)
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import Attachment
from app.main.blueprints.one_dev.utils.cancellation_checker import CancellationChecker

class BaseLLMProvider(ABC):
    """Abstract LLM interface"""

    def __init__(self, llm_type: str):
        self.llm_type = llm_type

    @abstractmethod
    async def build_llm_payload(
        self,
        llm_model: LLModels,
        attachment_data_task_map: Dict[int, asyncio.Task[ChatAttachmentDataWithObjectBytes]],
        prompt: Optional[UserAndSystemMessages] = None,
        attachments: List[Attachment] = [],
        tool_use_response: Optional[ToolUseResponseData] = None,
        previous_responses: List[MessageThreadDTO] = [],
        tools: Optional[List[ConversationTool]] = None,
        tool_choice: Literal["none", "auto", "required"] = "auto",
        feedback: Optional[str] = None,
        cache_config: PromptCacheConfig = PromptCacheConfig(tools=False, system_message=False, conversation=False),
        search_web: bool = False,
        disable_caching: bool = False,
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
        return ConfigManager.configs["LLM_MODELS"][model.value]

    async def call_service_client(
        self, llm_payload: Dict[str, Any], model: LLModels, checker: CancellationChecker, stream: bool = False, response_type: Optional[str] = None, session_id: Optional[int] = None
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
