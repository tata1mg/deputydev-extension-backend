from abc import ABC, abstractmethod
from typing import List, Optional, Type

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.dataclasses.main import LLMHandlerInputs
from app.backend_common.services.llm.prompts.base_feature_prompt_factory import BaseFeaturePromptFactory
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import QuerySolverInput
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData


class BaseQuerySolverAgent(ABC):
    """
    Base class for query solver agents.
    This class should be extended by specific query solver agents.
    """

    # this needs to be overridden by the subclass
    agent_name: str = "BaseQuerySolverAgent"
    description: str = "Base Query Solver Agent"
    prompt: Type[BaseFeaturePromptFactory]

    def __init__(self, previous_messages: Optional[List[int]] = None) -> None:
        """
        Initialize the agent with previous messages.

        :param previous_messages: Optional list of previous messages in the conversation.
        """
        self.previous_messages = previous_messages if previous_messages is not None else []

    @abstractmethod
    def get_llm_inputs(
        self, payload: QuerySolverInput, _client_data: ClientData, llm_model: LLModels
    ) -> LLMHandlerInputs:
        """
        Generate the inputs for the LLM handler based on the task and previous messages.
        :return: LLMHandlerInputs object containing the user and system messages.
        """

        raise NotImplementedError(f"{self.__class__.__name__}.get_tools() must be implemented by the subclass.")
