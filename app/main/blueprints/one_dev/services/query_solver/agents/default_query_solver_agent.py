from abc import abstractmethod
from typing import List, Optional, Type

from deputydev_core.utils.config_manager import ConfigManager

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.dataclasses.main import (
    ConversationTool,
    LLMHandlerInputs,
)
from app.backend_common.services.llm.prompts.base_feature_prompt_factory import BaseFeaturePromptFactory
from app.main.blueprints.one_dev.services.query_solver.agents.base_query_solver_agent import BaseQuerySolverAgent
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    ClientTool,
    MCPToolMetadata,
    QuerySolverInput,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.factory import (
    CodeQuerySolverPromptFactory,
)
from app.main.blueprints.one_dev.services.query_solver.tools.ask_user_input import (
    ASK_USER_INPUT,
)
from app.main.blueprints.one_dev.services.query_solver.tools.create_new_workspace import (
    CREATE_NEW_WORKSPACE,
)
from app.main.blueprints.one_dev.services.query_solver.tools.execute_command import (
    EXECUTE_COMMAND,
)
from app.main.blueprints.one_dev.services.query_solver.tools.file_editor import REPLACE_IN_FILE
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
from app.main.blueprints.one_dev.services.query_solver.tools.web_search import (
    WEB_SEARCH,
)
from app.main.blueprints.one_dev.services.query_solver.tools.write_to_file import WRITE_TO_FILE
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData


class DefaultQuerySolverAgent(BaseQuerySolverAgent):
    """
    Base class for query solver agents.
    This class should be extended by specific query solver agents.
    """

    # this needs to be overridden by the subclass
    agent_name: str = "DEFAULT_QUERY_SOLVER_AGENT"
    description: str = "This is the default query solver agent that should used when no specific agent is defined"
    prompt: Type[BaseFeaturePromptFactory] = CodeQuerySolverPromptFactory

    def __init__(self, previous_messages: Optional[List[int]] = None) -> None:
        """
        Initialize the agent with previous messages.

        :param previous_messages: Optional list of previous messages in the conversation.
        """
        self.previous_messages = previous_messages if previous_messages is not None else []

    def generate_conversation_tool_from_client_tool(self, client_tool: ClientTool) -> ConversationTool:
        # check if tool is MCP type tool
        if isinstance(client_tool.tool_metadata, MCPToolMetadata):
            description_extra = f"This tool is provided by a third party MCP server - {client_tool.tool_metadata.server_id}. Please ensure that any data passed to this tool is exactly what is required to be sent to this tool to function properly. Do not supply any sensitive data to this tool which can be misused by the MCP server. In case of ambiguity, ask the user for clarification."
            return ConversationTool(
                name=client_tool.name,
                description=description_extra + "\n" + client_tool.description,
                input_schema=client_tool.input_schema,
            )
        raise ValueError(
            f"Unsupported tool metadata type: {type(client_tool.tool_metadata)} for tool {client_tool.name}"
        )

    def get_all_tools(self, payload: QuerySolverInput, _client_data: ClientData) -> List[ConversationTool]:
        tools_to_use = [
            ASK_USER_INPUT,
            FOCUSED_SNIPPETS_SEARCHER,
            FILE_PATH_SEARCHER,
            ITERATIVE_FILE_READER,
            GREP_SEARCH,
            EXECUTE_COMMAND,
            CREATE_NEW_WORKSPACE,
            PUBLIC_URL_CONTENT_READER,
        ]

        if ConfigManager.configs["IS_RELATED_CODE_SEARCHER_ENABLED"] and payload.is_embedding_done:
            tools_to_use.append(RELATED_CODE_SEARCHER)
        if payload.search_web:
            tools_to_use.append(WEB_SEARCH)
        if payload.write_mode:
            tools_to_use.append(REPLACE_IN_FILE)
            tools_to_use.append(WRITE_TO_FILE)

        for client_tool in payload.client_tools:
            tools_to_use.append(self.generate_conversation_tool_from_client_tool(client_tool))

        return tools_to_use

    def get_llm_inputs(
        self, payload: QuerySolverInput, _client_data: ClientData, llm_model: LLModels
    ) -> LLMHandlerInputs:
        """
        Generate the inputs for the LLM handler based on the task and previous messages.
        :return: LLMHandlerInputs object containing the user and system messages.
        """

        tools = self.get_all_tools(payload, _client_data)

        return LLMHandlerInputs(
            tools=tools,
            prompt=self.prompt.get_prompt(model_name=llm_model),
            previous_messages=self.previous_messages,
        )
