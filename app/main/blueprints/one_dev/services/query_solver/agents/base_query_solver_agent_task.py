from abc import ABC, abstractmethod
from typing import List, Optional

from app.backend_common.models.dto.message_thread_dto import MessageThreadDTO
from app.backend_common.services.llm.dataclasses.main import LLMHandlerInputs
from app.backend_common.services.llm.prompts.base_prompt import BasePrompt


class BaseQuerySolverAgent(ABC):
    """
    Base class for query solver agents.
    This class should be extended by specific query solver agents.
    """

    # this needs to be overridden by the subclass
    agent_name: str = "BaseQuerySolverAgent"
    description: str = "Base Query Solver Agent"

    def __init__(self, previous_messages: Optional[List[MessageThreadDTO]] = None) -> None:
        """
        Initialize the agent with previous messages.

        :param previous_messages: Optional list of previous messages in the conversation.
        """
        self.previous_messages = previous_messages if previous_messages is not None else []

    @abstractmethod
    def generate_llm_inputs(self) -> LLMHandlerInputs:
        """
        Generate the inputs for the LLM handler based on the task and previous messages.
        :return: LLMHandlerInputs object containing the user and system messages.
        """

        raise NotImplementedError(
            f"{self.__class__.__name__}.generate_llm_inputs() must be implemented by the subclass."
        )

    @abstractmethod
    def get_llm_response_handler(self) -> BasePrompt:
        """
        Get the response handler for the task.
        This method should be implemented by the subclass to handle the response from the LLM.

        :return: A BasePrompt object representing the response handler.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__}.get_llm_response_handler() must be implemented by the subclass."
        )
