from typing import List, Optional, Tuple, Type

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.dataclasses.agent import LLMHandlerInputs
from app.backend_common.services.llm.dataclasses.main import ConversationTool
from app.backend_common.services.llm.prompts.base_feature_prompt_factory import BaseFeaturePromptFactory
from app.backend_common.utils.dataclasses.main import ClientData
from app.main.blueprints.one_dev.models.dto.agent_chats import AgentChatDTO
from app.main.blueprints.one_dev.services.query_solver.agents.base_query_solver_agent import QuerySolverAgent
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import QuerySolverInput
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.custom_code_query_solver.factory import (
    CustomCodeQuerySolverPromptFactory,
)


class CustomQuerySolverAgent(QuerySolverAgent):
    """
    Query solver agent for custom tasks.
    """

    prompt_factory: Type[BaseFeaturePromptFactory] = CustomCodeQuerySolverPromptFactory

    def __init__(self, agent_name: str, agent_description: str, allowed_tools: List[str], prompt_intent: str) -> None:
        """
        Initialize the agent with previous messages.

        :param previous_messages: Optional list of previous messages in the conversation.
        """
        super().__init__(agent_name, agent_description)
        self.allowed_tools = allowed_tools
        self.prompt_intent = prompt_intent

    def _filter_tools(self, tools: List[ConversationTool]) -> List[ConversationTool]:
        """
        Filter the tools based on the allowed tools for this agent.
        :param tools: List of all available tools.
        :return: Filtered list of tools.
        """
        return [tool for tool in tools if tool.name in self.allowed_tools]

    def get_all_tools(self, payload: QuerySolverInput, _client_data: ClientData) -> List[ConversationTool]:
        """
        Get all tools available for this agent, filtered by allowed tools.
        :param payload: QuerySolverInput containing the task details.
        :param _client_data: ClientData containing client information.
        :return: List of ConversationTool objects.
        """
        all_tools = self.get_all_first_party_tools(payload, _client_data)
        all_tools = self._filter_tools(all_tools)
        all_tools.extend(self.get_all_client_tools(payload, _client_data))

        return all_tools

    async def get_llm_inputs_and_previous_queries(
        self,
        payload: QuerySolverInput,
        _client_data: ClientData,
        llm_model: LLModels,
        new_query_chat: Optional[AgentChatDTO] = None,
    ) -> Tuple[LLMHandlerInputs, List[str]]:
        """
        Generate the inputs for the LLM handler based on the task and previous messages.
        :return: LLMHandlerInputs object containing the user and system messages.
        """

        tools = self.get_all_tools(payload, _client_data)
        messages, previous_queries = await self._get_conversation_turns_and_previous_queries(
            payload, _client_data, new_query_chat
        )
        return LLMHandlerInputs(
            tools=tools,
            prompt=self.prompt_factory.get_prompt(model_name=llm_model),
            messages=messages,
            extra_prompt_vars={
                "prompt_intent": self.prompt_intent,
            },
        ), previous_queries
