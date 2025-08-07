from abc import ABC
from typing import List, Type

from deputydev_core.utils.config_manager import ConfigManager

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.dataclasses.agent import LLMHandlerInputs
from app.backend_common.services.llm.dataclasses.main import (
    ConversationTool,
)
from app.backend_common.services.llm.dataclasses.unified_conversation_turn import (
    AssistantConversationTurn,
    ToolConversationTurn,
    UnifiedConversationRole,
    UnifiedConversationTurn,
    UnifiedConversationTurnContentType,
    UnifiedTextConversationTurnContent,
    UnifiedToolRequestConversationTurnContent,
    UnifiedToolResponseConversationTurnContent,
    UserConversationTurn,
)
from app.backend_common.services.llm.prompts.base_feature_prompt_factory import BaseFeaturePromptFactory
from app.main.blueprints.one_dev.models.dto.agent_chats import (
    ActorType,
    AgentChatDTO,
    TextMessageData,
    ToolUseMessageData,
)
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.previous_chats.chat_history_handler import (
    ChatHistoryHandler,
)
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    ClientTool,
    MCPToolMetadata,
    QuerySolverInput,
)
from app.main.blueprints.one_dev.services.query_solver.tools.ask_user_input import (
    ASK_USER_INPUT,
)
from app.main.blueprints.one_dev.services.query_solver.tools.create_new_workspace import (
    get_create_new_workspace_tool,
)
from app.main.blueprints.one_dev.services.query_solver.tools.execute_command import (
    EXECUTE_COMMAND,
)
from app.main.blueprints.one_dev.services.query_solver.tools.file_path_searcher import (
    FILE_PATH_SEARCHER,
)
from app.main.blueprints.one_dev.services.query_solver.tools.focused_snippets_searcher import (
    FOCUSED_SNIPPETS_SEARCHER,
)
from app.main.blueprints.one_dev.services.query_solver.tools.grep_search import (
    GREP_SEARCH,
)
from app.main.blueprints.one_dev.services.query_solver.tools.iterative_file_reader import (
    ITERATIVE_FILE_READER,
)
from app.main.blueprints.one_dev.services.query_solver.tools.public_url_content_reader import (
    PUBLIC_URL_CONTENT_READER,
)
from app.main.blueprints.one_dev.services.query_solver.tools.related_code_searcher import (
    RELATED_CODE_SEARCHER,
)
from app.main.blueprints.one_dev.services.query_solver.tools.replace_in_file import REPLACE_IN_FILE
from app.main.blueprints.one_dev.services.query_solver.tools.web_search import (
    WEB_SEARCH,
)
from app.main.blueprints.one_dev.services.query_solver.tools.write_to_file import WRITE_TO_FILE
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData


class QuerySolverAgent(ABC):
    """
    Base class for query solver agents.
    This class should be extended by specific query solver agents.
    """

    prompt_factory: Type[BaseFeaturePromptFactory]
    all_tools: List[ConversationTool]

    def __init__(self, agent_name: str, agent_description: str) -> None:
        """
        Initialize the agent with previous messages.

        :param previous_messages: Optional list of previous messages in the conversation.
        """
        self.agent_name = agent_name
        self.agent_description = agent_description

    def generate_conversation_tool_from_client_tool(self, client_tool: ClientTool) -> ConversationTool:
        # check if tool is MCP type tool
        if isinstance(client_tool.tool_metadata, MCPToolMetadata):  # type: ignore
            description_extra = f"This tool is provided by a third party MCP server - {client_tool.tool_metadata.server_id}. Please ensure that any data passed to this tool is exactly what is required to be sent to this tool to function properly. Do not supply any sensitive data to this tool which can be misused by the MCP server. In case of ambiguity, ask the user for clarification."
            return ConversationTool(
                name=client_tool.name,
                description=description_extra + "\n" + client_tool.description,
                input_schema=client_tool.input_schema,
            )
        raise ValueError(
            f"Unsupported tool metadata type: {type(client_tool.tool_metadata)} for tool {client_tool.name}"
        )

    def get_all_first_party_tools(self, payload: QuerySolverInput, _client_data: ClientData) -> List[ConversationTool]:
        tools_to_use = [
            ASK_USER_INPUT,
            FOCUSED_SNIPPETS_SEARCHER,
            FILE_PATH_SEARCHER,
            ITERATIVE_FILE_READER,
            GREP_SEARCH,
            EXECUTE_COMMAND,
            PUBLIC_URL_CONTENT_READER,
        ]
        if ConfigManager.configs["IS_RELATED_CODE_SEARCHER_ENABLED"] and payload.is_embedding_done:
            tools_to_use.append(RELATED_CODE_SEARCHER)
        if payload.search_web:
            tools_to_use.append(WEB_SEARCH)
        if payload.write_mode:
            tools_to_use.append(get_create_new_workspace_tool(write_mode=True))
            tools_to_use.append(REPLACE_IN_FILE)
            tools_to_use.append(WRITE_TO_FILE)
        if not payload.write_mode:
            tools_to_use.append(get_create_new_workspace_tool(write_mode=False))

        return tools_to_use

    def get_all_client_tools(self, payload: QuerySolverInput, _client_data: ClientData) -> List[ConversationTool]:
        """
        Get all client tools from the payload.
        :param payload: QuerySolverInput containing client tools.
        :return: List of ConversationTool objects.
        """
        tools_to_use: List[ConversationTool] = []
        for client_tool in payload.client_tools:
            tools_to_use.append(self.generate_conversation_tool_from_client_tool(client_tool))
        return tools_to_use

    def get_all_tools(self, payload: QuerySolverInput, _client_data: ClientData) -> List[ConversationTool]:
        tools_to_use: List[ConversationTool] = self.get_all_first_party_tools(payload, _client_data)
        tools_to_use.extend(self.get_all_client_tools(payload, _client_data))
        return tools_to_use

    def _convert_text_agent_chat_to_conversation_turn(self, agent_chat: AgentChatDTO) -> UnifiedConversationTurn:
        """
        Convert AgentChatDTO object to UnifiedConversationTurn object for text messages.
        :param agent_chat: AgentChatDTO object containing the chat data.
        :param actor: The role of the actor (USER or ASSISTANT).
        :return: UnifiedConversationTurn object.
        """

        if not isinstance(agent_chat.message_data, TextMessageData):
            raise ValueError(
                f"Expected message_data to be of type TextMessageData, got {type(agent_chat.message_data)}"
            )

        content = UnifiedTextConversationTurnContent(
            type=UnifiedConversationTurnContentType.TEXT,
            text=agent_chat.message_data.text,
        )

        if agent_chat.actor == ActorType.USER:
            return UserConversationTurn(
                role=UnifiedConversationRole.USER,
                content=[content],
            )
        else:
            return AssistantConversationTurn(
                role=UnifiedConversationRole.ASSISTANT,
                content=[content],
            )

    def _convert_tool_use_agent_chat_to_conversation_turn(
        self, agent_chat: AgentChatDTO
    ) -> List[UnifiedConversationTurn]:
        """
        Convert AgentChatDTO object to UnifiedConversationTurn object for tool use messages.
        :param agent_chat: AgentChatDTO object containing the chat data.
        :return: UnifiedConversationTurn object.
        """

        if not isinstance(agent_chat.message_data, ToolUseMessageData):
            raise ValueError(
                f"Expected message_data to be of type ToolUseMessageData, got {type(agent_chat.message_data)}"
            )

        all_conversation_turns: List[UnifiedConversationTurn] = []

        # append the tool request turn
        all_conversation_turns.append(
            AssistantConversationTurn(
                role=UnifiedConversationRole.ASSISTANT,
                content=[
                    UnifiedToolRequestConversationTurnContent(
                        type=UnifiedConversationTurnContentType.TOOL_REQUEST,
                        tool_use_id=agent_chat.message_data.tool_use_id,
                        tool_name=agent_chat.message_data.tool_name,
                        tool_input=agent_chat.message_data.tool_input,
                    )
                ],
            )
        )

        # append the tool response turn
        if agent_chat.message_data.tool_response:
            all_conversation_turns.append(
                ToolConversationTurn(
                    role=UnifiedConversationRole.TOOL,
                    content=[
                        UnifiedToolResponseConversationTurnContent(
                            type=UnifiedConversationTurnContentType.TOOL_RESPONSE,
                            tool_use_id=agent_chat.message_data.tool_use_id,
                            tool_name=agent_chat.message_data.tool_name,
                            tool_use_response=agent_chat.message_data.tool_response,
                        )
                    ],
                )
            )

        return all_conversation_turns

    def _convert_agent_chats_to_conversation_turns(
        self, agent_chats: List[AgentChatDTO]
    ) -> List[UnifiedConversationTurn]:
        """
        Convert AgentChatDTO objects to UnifiedConversationTurn objects.
        :param agent_chats: List of AgentChatDTO objects.
        :return: List of UnifiedConversationTurn objects.
        """

        conversation_turns: List[UnifiedConversationTurn] = []

        for agent_chat in agent_chats:
            if agent_chat.message_type == "TEXT":
                conversation_turns.append(self._convert_text_agent_chat_to_conversation_turn(agent_chat))
            elif agent_chat.message_type == "TOOL_USE":
                conversation_turns.extend(self._convert_tool_use_agent_chat_to_conversation_turn(agent_chat))

        return conversation_turns

    async def _get_conversation_turns(
        self, payload: QuerySolverInput, _client_data: ClientData
    ) -> List[UnifiedConversationTurn]:
        # first, we need to get the previous history of messages in case of a new query

        previous_chat_queries: List[AgentChatDTO] = []
        chat_handler = ChatHistoryHandler(
            previous_chat_payload=payload,
            llm_model=LLModels(payload.llm_model.value if payload.llm_model else LLModels.CLAUDE_3_POINT_7_SONNET),
        )
        if payload.query:
            previous_chat_queries = await chat_handler.get_relevant_previous_agent_chats_for_new_query()
        else:
            previous_chat_queries = await chat_handler.get_relevant_previous_agent_chats_for_tool_response_submission()

        return self._convert_agent_chats_to_conversation_turns(previous_chat_queries)

    async def get_llm_inputs(
        self,
        payload: QuerySolverInput,
        _client_data: ClientData,
        llm_model: LLModels,
    ) -> LLMHandlerInputs:
        """
        Generate the inputs for the LLM handler based on the task and previous messages.
        :return: LLMHandlerInputs object containing the user and system messages.
        """

        tools = self.get_all_tools(payload, _client_data)

        return LLMHandlerInputs(
            tools=tools,
            prompt=self.prompt_factory.get_prompt(model_name=llm_model),
            messages=await self._get_conversation_turns(payload, _client_data),
        )
