import textwrap
from asyncio import Task
from typing import Dict, List, Optional, Tuple, Type

from deputydev_core.llm_handler.dataclasses.agent import LLMHandlerInputs
from deputydev_core.llm_handler.dataclasses.main import (
    ConversationTool,
)
from deputydev_core.llm_handler.dataclasses.unified_conversation_turn import (
    AssistantConversationTurn,
    ToolConversationTurn,
    UnifiedConversationRole,
    UnifiedConversationTurn,
    UnifiedConversationTurnContentType,
    UnifiedImageConversationTurnContent,
    UnifiedTextConversationTurnContent,
    UnifiedToolRequestConversationTurnContent,
    UnifiedToolResponseConversationTurnContent,
    UserConversationTurn,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels
from deputydev_core.utils.config_manager import ConfigManager

from app.backend_common.repository.chat_attachments.repository import ChatAttachmentsRepository
from app.backend_common.services.chat_file_upload.chat_file_upload import ChatFileUpload
from app.backend_common.services.chat_file_upload.dataclasses.chat_file_upload import (
    Attachment,
    ChatAttachmentDataWithObjectBytes,
)
from app.backend_common.utils.dataclasses.main import ClientData
from app.main.blueprints.one_dev.models.dto.agent_chats import (
    ActorType,
    AgentChatDTO,
    CodeBlockData,
    TaskPlanData,
    TextMessageData,
    ThinkingInfoData,
    ToolUseMessageData,
)
from app.main.blueprints.one_dev.services.query_solver.agent.chat_history_handler.chat_history_handler import (
    ChatHistoryHandler,
)
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    ClassFocusItem,
    ClientTool,
    CodeSnippetFocusItem,
    DirectoryFocusItem,
    FileFocusItem,
    FunctionFocusItem,
    MCPToolMetadata,
    QuerySolverInput,
    Repository,
    UrlFocusItem,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.factory import (
    CodeQuerySolverPromptFactory,
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
from app.main.blueprints.one_dev.services.query_solver.tools.get_usage_tool import (
    GET_USAGE_TOOL,
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
from app.main.blueprints.one_dev.services.query_solver.tools.resolve_import_tool import RESOLVE_IMPORT_TOOL
from app.main.blueprints.one_dev.services.query_solver.tools.web_search import (
    WEB_SEARCH,
)
from app.main.blueprints.one_dev.services.query_solver.tools.write_to_file import WRITE_TO_FILE


class QuerySolverAgent:
    """
    Base class for query solver agents.
    This class should be extended by specific query solver agents.
    """

    prompt_factory: Type[CodeQuerySolverPromptFactory] = CodeQuerySolverPromptFactory
    all_tools: List[ConversationTool]

    def __init__(
        self,
        agent_name: str,
        agent_description: str,
        allowed_tools: Optional[List[str]] = None,
        prompt_intent: Optional[str] = None,
    ) -> None:
        """
        Initialize the agent with previous messages.

        :param previous_messages: Optional list of previous messages in the conversation.
        """
        self.agent_name = agent_name
        self.agent_description = agent_description
        self.attachment_data_task_map: Dict[int, Task[ChatAttachmentDataWithObjectBytes]] = {}
        self.allowed_tools = allowed_tools
        self.prompt_intent = prompt_intent

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
        if payload.is_lsp_ready:
            tools_to_use.append(GET_USAGE_TOOL)
            tools_to_use.append(RESOLVE_IMPORT_TOOL)
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

    def get_repository_context(self, repositories: List[Repository]) -> str:
        working_repo = next(repo for repo in repositories if repo.is_working_repository)
        context_repos = [repo for repo in repositories if not repo.is_working_repository]
        context_repos_str = ""
        for index, context_repo in enumerate(context_repos):
            context_repos_str += f"""
                <context_repository_{index + 1}>
                    <absolute_repo_path>{context_repo.repo_path}</absolute_repo_path>
                    <repo_name>{context_repo.repo_name}</repo_name>
                    <root_directory_context>
                    {context_repo.root_directory_context}
                    </root_directory_context>
                </context_repository_{index + 1}>
                """

        return textwrap.dedent(f"""
            ====
            <repository_context>
            You are working with two types of repositories:
            <working_repository>
                <purpose>The primary repository where you will make changes and apply modifications</purpose>
                <access_level>Full read/write access</access_level>
                <allowed_operations>All read and write operations</allowed_operations>
                <restrictions>No restrictions</restrictions>
                <absolute_repo_path>{working_repo.repo_path}</absolute_repo_path>
                <repo_name>{working_repo.repo_name}</repo_name>
                <root_directory_context>{working_repo.root_directory_context}</root_directory_context>
            </working_repository>
            <context_repositories>
                <purpose>Reference repositories for gathering context, examples, and understanding patterns</purpose>
                <access_level>Read-only access</access_level>
                <allowed_operations>Read operations only. Only use those tools that are reading context from the repository</allowed_operations>
                <restrictions>
                1. NO write operations allowed
                2. NO file creation or modification
                3. NO diff application
                </restrictions>
                <list_of_context_repositories>
                    {context_repos_str}
                </list_of_context_repositories>
            </context_repositories>
            </repository_context>
            ====
            """)

    async def _get_unified_user_conv_turns(  # noqa: C901
        self, message_data: TextMessageData, prompt_intent: Optional[str] = None
    ) -> List[UnifiedConversationTurn]:
        """
        Get unified text conversation turn content for user messages.
        :param message_data: TextMessageData containing the text message.
        :return: UnifiedTextConversationTurnContent object.
        """

        all_turns: List[UnifiedConversationTurn] = []
        # first process attachments
        for attachment in message_data.attachments:
            if attachment.attachment_id in self.attachment_data_task_map:
                image_data = await self.attachment_data_task_map[attachment.attachment_id]
                all_turns.append(
                    UserConversationTurn(
                        role=UnifiedConversationRole.USER,
                        content=[
                            UnifiedImageConversationTurnContent(
                                type=UnifiedConversationTurnContentType.IMAGE,
                                bytes_data=image_data.object_bytes,
                                image_mimetype=image_data.attachment_metadata.file_type,
                            )
                        ],
                    )
                )

        text = f"<task>{message_data.text}</task>"

        if prompt_intent:
            text += f"""
            The user's query is focused on creating a backend application, so you should focus on backend technologies and frameworks.
            You should follow the below guidelines while creating the backend application:
            {prompt_intent}
        """

        if message_data.focus_items:
            code_snippet_based_items = [
                item
                for item in message_data.focus_items
                if isinstance(item, CodeSnippetFocusItem)
                or isinstance(item, FileFocusItem)
                or isinstance(item, ClassFocusItem)
                or isinstance(item, FunctionFocusItem)
            ]
            if code_snippet_based_items:
                text += "The user has asked to focus on the following\n"
                for focus_item in code_snippet_based_items:
                    text += (
                        "<item>"
                        + f"<type>{focus_item.type.value}</type>"
                        + (f"<value>{focus_item.value}</value>" if focus_item.value else "")
                        + (f"<path>{focus_item.path}</path>")
                        + "\n".join([chunk.get_xml() for chunk in focus_item.chunks])
                        + "</item>"
                    )

            directory_items = [item for item in message_data.focus_items if isinstance(item, DirectoryFocusItem)]
            if directory_items:
                text += "\nThe user has also asked to explore the contents of the following directories:\n"
                for directory_item in directory_items:
                    text += (
                        "<item>" + "<type>directory</type>" + f"<path>{directory_item.path}</path>" + "<structure>\n"
                    )
                    for entry in directory_item.structure or []:
                        label = "file" if entry.type == "file" else "folder"
                        text += f"{label}: {entry.name}\n"
                    text += "</structure></item>"

            url_focus_items = [item for item in message_data.focus_items if isinstance(item, UrlFocusItem)]
            if url_focus_items:
                text += f"\nThe user has also provided the following URLs for reference: {[url.url for url in url_focus_items]}\n"
        if message_data.vscode_env:
            text += f"""\n====

            Below is the information about the current vscode environment:
            {message_data.vscode_env}

            ===="""

        if message_data.repositories:
            text += textwrap.dedent(self.get_repository_context(message_data.repositories))

        all_turns.append(
            UserConversationTurn(
                role=UnifiedConversationRole.USER,
                content=[
                    UnifiedTextConversationTurnContent(
                        type=UnifiedConversationTurnContentType.TEXT,
                        text=textwrap.dedent(text).strip(),
                    )
                ],
            )
        )

        return all_turns

    async def _convert_text_agent_chat_to_conversation_turn(
        self, agent_chat: AgentChatDTO, prompt_intent: Optional[str] = None
    ) -> List[UnifiedConversationTurn]:
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

        if agent_chat.actor == ActorType.USER:
            return await self._get_unified_user_conv_turns(agent_chat.message_data, prompt_intent)
        else:
            return [
                AssistantConversationTurn(
                    role=UnifiedConversationRole.ASSISTANT,
                    content=[
                        UnifiedTextConversationTurnContent(
                            type=UnifiedConversationTurnContentType.TEXT,
                            text=agent_chat.message_data.text,
                        )
                    ],
                )
            ]

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
        else:
            all_conversation_turns.append(
                ToolConversationTurn(
                    role=UnifiedConversationRole.TOOL,
                    content=[
                        UnifiedToolResponseConversationTurnContent(
                            type=UnifiedConversationTurnContentType.TOOL_RESPONSE,
                            tool_use_id=agent_chat.message_data.tool_use_id,
                            tool_name=agent_chat.message_data.tool_name,
                            tool_use_response={"response": "NO_RESPONSE"},
                        )
                    ],
                )
            )

        return all_conversation_turns

    def _convert_thinking_agent_chat_to_conversation_turn(
        self, agent_chat: AgentChatDTO
    ) -> List[UnifiedConversationTurn]:
        """
        Convert AgentChatDTO object to UnifiedConversationTurn object for thinking messages.
        :param agent_chat: AgentChatDTO object containing the chat data.
        :return: UnifiedConversationTurn object.
        """

        if not isinstance(agent_chat.message_data, ThinkingInfoData):
            raise ValueError(
                f"Expected message_data to be of type ThinkingInfoData, got {type(agent_chat.message_data)}"
            )
        if agent_chat.message_data.ignore_in_chat:
            return []
        return [
            AssistantConversationTurn(
                role=UnifiedConversationRole.ASSISTANT,
                content=[
                    UnifiedTextConversationTurnContent(
                        type=UnifiedConversationTurnContentType.TEXT,
                        text=agent_chat.message_data.thinking_summary,
                    )
                ],
            )
        ]

    def _convert_code_block_agent_chat_to_conversation_turn(
        self, agent_chat: AgentChatDTO
    ) -> List[UnifiedConversationTurn]:
        """
        Convert AgentChatDTO object to UnifiedConversationTurn object for code block messages.
        :param agent_chat: AgentChatDTO object containing the chat data.
        :return: UnifiedConversationTurn object.
        """

        if not isinstance(agent_chat.message_data, CodeBlockData):
            raise ValueError(f"Expected message_data to be of type CodeBlockData, got {type(agent_chat.message_data)}")

        return [
            AssistantConversationTurn(
                role=UnifiedConversationRole.ASSISTANT,
                content=[
                    UnifiedTextConversationTurnContent(
                        type=UnifiedConversationTurnContentType.TEXT,
                        text=agent_chat.message_data.code,
                    )
                ],
            )
        ]

    def _convert_task_plan_agent_chat_to_conversation_turn(
        self, agent_chat: AgentChatDTO
    ) -> List[UnifiedConversationTurn]:
        """
        Convert AgentChatDTO object to UnifiedConversationTurn object for task plan messages.
        :param agent_chat: AgentChatDTO object containing the chat data.
        :return: UnifiedConversationTurn object.
        """

        if not isinstance(agent_chat.message_data, TaskPlanData):
            raise ValueError(f"Expected message_data to be of type TaskPlanData, got {type(agent_chat.message_data)}")

        return [
            AssistantConversationTurn(
                role=UnifiedConversationRole.ASSISTANT,
                content=[
                    UnifiedTextConversationTurnContent(
                        type=UnifiedConversationTurnContentType.TEXT,
                        text=f"<task_plan>{''.join([f'<step>{step.step_description}<completed>{str(step.is_completed).lower()}</completed></step>' for step in agent_chat.message_data.latest_plan_steps])}</task_plan>",
                    )
                ],
            )
        ]

    async def _convert_agent_chats_to_conversation_turns(
        self, agent_chats: List[AgentChatDTO], prompt_intent: Optional[str] = None
    ) -> List[UnifiedConversationTurn]:
        """
        Convert AgentChatDTO objects to UnifiedConversationTurn objects.
        :param agent_chats: List of AgentChatDTO objects.
        :return: List of UnifiedConversationTurn objects.
        """

        conversation_turns: List[UnifiedConversationTurn] = []

        for agent_chat in agent_chats:
            if agent_chat.message_type == "TEXT":
                conversation_turns.extend(
                    await self._convert_text_agent_chat_to_conversation_turn(agent_chat, prompt_intent)
                )
            elif agent_chat.message_type == "TOOL_USE":
                conversation_turns.extend(self._convert_tool_use_agent_chat_to_conversation_turn(agent_chat))
            elif agent_chat.message_type == "THINKING":
                conversation_turns.extend(self._convert_thinking_agent_chat_to_conversation_turn(agent_chat))
            elif agent_chat.message_type == "CODE_BLOCK":
                conversation_turns.extend(self._convert_code_block_agent_chat_to_conversation_turn(agent_chat))
            elif agent_chat.message_type == "TASK_PLAN":
                conversation_turns.extend(self._convert_task_plan_agent_chat_to_conversation_turn(agent_chat))

        return conversation_turns

    async def get_all_chat_attachments(self, previous_chat_queries: List[AgentChatDTO]) -> List[Attachment]:
        """
        Get all chat attachment IDs from the previous chat queries.
        :param previous_chat_queries: List of AgentChatDTO objects containing previous chat data.
        :return: List of chat attachment IDs.
        """
        attachment_ids: List[int] = []
        for agent_chat in previous_chat_queries:
            if (
                agent_chat.message_data
                and isinstance(agent_chat.message_data, TextMessageData)
                and agent_chat.message_data.attachments
            ):
                attachment_ids.extend(attachment.attachment_id for attachment in agent_chat.message_data.attachments)
        # filter all attachments which are not deleted
        all_attachments_from_db = await ChatAttachmentsRepository.get_attachments_by_ids(attachment_ids)
        filtered_attachment_ids = [
            attachment.id for attachment in all_attachments_from_db if attachment.status != "deleted"
        ]
        return [Attachment(attachment_id=attachment_id) for attachment_id in filtered_attachment_ids]

    async def _get_conversation_turns_and_previous_queries(
        self,
        payload: QuerySolverInput,
        _client_data: ClientData,
        new_query_chat: Optional[AgentChatDTO] = None,
        prompt_intent: Optional[str] = None,
    ) -> Tuple[List[UnifiedConversationTurn], List[str]]:
        # first, we need to get the previous history of messages in case of a new query

        previous_chat_queries: List[AgentChatDTO] = []
        chat_handler = ChatHistoryHandler(
            previous_chat_payload=payload,
            llm_model=LLModels(payload.llm_model.value if payload.llm_model else LLModels.CLAUDE_3_POINT_7_SONNET),
        )
        previous_queries: List[str] = []
        if payload.query:
            if not new_query_chat:
                raise ValueError("new_query_chat must be provided when payload.query is present")
            (
                previous_chat_queries,
                previous_queries,
            ) = await chat_handler.get_relevant_previous_agent_chats_for_new_query(new_query_chat)
        else:
            (
                previous_chat_queries,
                previous_queries,
            ) = await chat_handler.get_relevant_previous_agent_chats_for_tool_response_submission()

        filtered_attachments = await self.get_all_chat_attachments(previous_chat_queries)
        self.attachment_data_task_map = ChatFileUpload.get_attachment_data_task_map(filtered_attachments)

        return await self._convert_agent_chats_to_conversation_turns(
            previous_chat_queries, prompt_intent
        ), previous_queries

    def _filter_tools(self, tools: List[ConversationTool]) -> List[ConversationTool]:
        """
        Filter the tools based on the allowed tools for this agent.
        :param tools: List of all available tools.
        :return: Filtered list of tools.
        """
        return [
            tool
            for tool in tools
            if ((self.allowed_tools and tool.name in self.allowed_tools) or not self.allowed_tools)
        ]

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
            payload, _client_data, new_query_chat, self.prompt_intent
        )
        return LLMHandlerInputs(
            tools=tools,
            prompt=self.prompt_factory.get_prompt(model_name=llm_model),
            messages=messages,
            extra_prompt_vars={
                "prompt_intent": self.prompt_intent,
            },
        ), previous_queries
