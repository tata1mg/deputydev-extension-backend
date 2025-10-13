import asyncio
from typing import Any, Dict, List
from uuid import uuid4

from deputydev_core.llm_handler.dataclasses.main import (
    NonStreamingParsedLLMCallResponse,
)
from deputydev_core.llm_handler.dataclasses.unified_conversation_turn import (
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
from deputydev_core.llm_handler.models.dto.message_thread_dto import (
    LLModels,
)
from deputydev_core.services.chunking.chunk_info import ChunkInfo, ChunkSourceDetails

from app.backend_common.services.llm.llm_service_manager import LLMServiceManager
from app.backend_common.utils.dataclasses.main import ClientData
from app.main.blueprints.one_dev.models.dto.agent_chats import (
    ActorType,
    AgentChatCreateRequest,
    AgentChatDTO,
    AgentChatUpdateRequest,
    CodeBlockData,
    MessageType,
    TextMessageData,
    ToolUseMessageData,
)
from app.main.blueprints.one_dev.models.dto.job import JobDTO
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    CodeSelectionInput,
    CodeSnippetFocusItem,
    InlineEditInput,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.one_dev.services.query_solver.tools.get_usage_tool import GET_USAGE_TOOL
from app.main.blueprints.one_dev.services.query_solver.tools.grep_search import GREP_SEARCH
from app.main.blueprints.one_dev.services.query_solver.tools.iterative_file_reader import ITERATIVE_FILE_READER
from app.main.blueprints.one_dev.services.query_solver.tools.replace_in_file import REPLACE_IN_FILE
from app.main.blueprints.one_dev.services.query_solver.tools.task_completed import TASK_COMPLETION
from app.main.blueprints.one_dev.services.repository.agent_chats.repository import AgentChatsRepository
from app.main.blueprints.one_dev.services.repository.code_generation_job.main import (
    JobService,
)

from .prompts.factory import PromptFeatureFactory


class InlineEditGenerator:
    async def _get_conversation_turns_from_agent_chat_for_inline_edit(
        self, agent_chats: List[AgentChatDTO], llm_model: LLModels, payload: InlineEditInput
    ) -> List[UnifiedConversationTurn]:
        conv_turns: List[UnifiedConversationTurn] = []
        for agent_chat in agent_chats:
            if agent_chat.actor == ActorType.USER and isinstance(agent_chat.message_data, TextMessageData):
                prompt_handler = PromptFeatureFactory.get_prompt(
                    model_name=llm_model, feature=PromptFeatures.INLINE_EDITOR
                )(
                    {
                        "query": agent_chat.message_data.text,
                        "code_selection": CodeSelectionInput(
                            selected_text=agent_chat.message_data.focus_items[0].chunks[0].content,
                            file_path=agent_chat.message_data.focus_items[0].path,
                        )
                        if agent_chat.message_data.focus_items
                        and isinstance(agent_chat.message_data.focus_items[0], CodeSnippetFocusItem)
                        else None,
                        "deputy_dev_rules": None,
                        "relevant_chunks": [],
                        "is_lsp_ready": payload.is_lsp_ready,
                        "repo_path": payload.repo_path,
                    }
                )
                prompt_text = prompt_handler.get_prompt()
                conv_turns.append(
                    UserConversationTurn(
                        role=UnifiedConversationRole.USER,
                        content=[
                            UnifiedTextConversationTurnContent(
                                type=UnifiedConversationTurnContentType.TEXT,
                                text=prompt_text.user_message,
                            )
                        ],
                    )
                )

            if agent_chat.actor == ActorType.ASSISTANT:
                if isinstance(agent_chat.message_data, CodeBlockData):
                    conv_turns.append(
                        AssistantConversationTurn(
                            role=UnifiedConversationRole.ASSISTANT,
                            content=[
                                UnifiedTextConversationTurnContent(
                                    text=agent_chat.message_data.code,
                                )
                            ],
                        )
                    )
                elif isinstance(agent_chat.message_data, ToolUseMessageData) and agent_chat.message_data.tool_response:
                    conv_turns.append(
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

                    if agent_chat.message_data.tool_response:
                        conv_turns.append(
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

        return conv_turns

    async def _get_response_from_parsed_llm_response(
        self, parsed_llm_response: List[Dict[str, Any]], query_id: str, session_id: int, llm_model: LLModels
    ) -> Dict[str, Any]:
        code_snippets: List[Dict[str, Any]] = []
        tool_use_request: Dict[str, Any] = {}
        for response in parsed_llm_response:
            if "code_snippets" in response:
                code_snippets.extend(response["code_snippets"])
            if "type" in response and response["type"] == "TOOL_USE_REQUEST":
                tool_use_request = response

        if code_snippets:
            for snippet in code_snippets:
                await AgentChatsRepository.create_chat(
                    chat_data=AgentChatCreateRequest(
                        session_id=session_id,
                        message_type=MessageType.CODE_BLOCK,
                        message_data=CodeBlockData(
                            code=snippet["code"],
                            language=snippet["programming_language"],
                            file_path=snippet["file_path"],
                        ),
                        query_id=query_id,
                        actor=ActorType.ASSISTANT,
                        metadata={"is_inline_editor": True, "llm_model": llm_model.value},
                        previous_queries=[],
                    )
                )

        if tool_use_request:
            await AgentChatsRepository.create_chat(
                chat_data=AgentChatCreateRequest(
                    session_id=session_id,
                    message_type=MessageType.TOOL_USE,
                    message_data=ToolUseMessageData(
                        tool_name=tool_use_request["content"]["tool_name"],
                        tool_use_id=tool_use_request["content"]["tool_use_id"],
                        tool_input=tool_use_request["content"]["tool_input"],
                    ),
                    query_id=query_id,
                    actor=ActorType.ASSISTANT,
                    metadata={"is_inline_editor": True, "llm_model": llm_model.value},
                    previous_queries=[],
                )
            )

        return {
            "code_snippets": code_snippets if code_snippets else None,
            "tool_use_request": tool_use_request if tool_use_request else None,
        }

    async def get_inline_edit_diff_suggestion(
        self, payload: InlineEditInput, client_data: ClientData
    ) -> Dict[str, Any]:
        llm_handler = LLMServiceManager().create_llm_handler(
            prompt_factory=PromptFeatureFactory,
            prompt_features=PromptFeatures,
        )
        tools_to_use = [ITERATIVE_FILE_READER, GREP_SEARCH, REPLACE_IN_FILE]

        if payload.llm_model and LLModels(payload.llm_model.value) == LLModels.GPT_4_POINT_1:
            tools_to_use.append(TASK_COMPLETION)
            payload.tool_choice = "required"
        if payload.is_lsp_ready:
            tools_to_use.append(GET_USAGE_TOOL)

        if payload.tool_use_response:
            all_chats_for_session = await AgentChatsRepository.get_chats_by_session_id(session_id=payload.session_id)
            agent_chat_with_tool_call = next(
                (
                    chat
                    for chat in all_chats_for_session
                    if isinstance(chat.message_data, ToolUseMessageData)
                    and chat.message_data.tool_use_id == payload.tool_use_response.tool_use_id
                ),
                None,
            )
            if not agent_chat_with_tool_call or not isinstance(
                agent_chat_with_tool_call.message_data, ToolUseMessageData
            ):
                raise ValueError("No matching agent chat found for the provided tool use response.")
            agent_chat_with_tool_call.message_data.tool_response = payload.tool_use_response.response

            # update the agent chat in the database
            await AgentChatsRepository.update_chat(
                chat_id=agent_chat_with_tool_call.id,
                update_data=AgentChatUpdateRequest(message_data=agent_chat_with_tool_call.message_data),
            )
            conversation_turns = await self._get_conversation_turns_from_agent_chat_for_inline_edit(
                agent_chats=all_chats_for_session, llm_model=LLModels(payload.llm_model.value), payload=payload
            )

            llm_response = await llm_handler.start_llm_query(
                session_id=payload.session_id,
                tools=tools_to_use,
                stream=False,
                parallel_tool_calls=True,
                tool_choice="required",
                conversation_turns=conversation_turns,
                prompt_feature=PromptFeatures.INLINE_EDITOR,
                llm_model=LLModels(payload.llm_model.value),
                prompt_vars={
                    "code_selection": payload.code_selection,
                    "deputy_dev_rules": None,
                    "relevant_chunks": [],
                    "query": payload.query,
                    "is_lsp_ready": payload.is_lsp_ready,
                    "repo_path": payload.repo_path,
                },
            )

            if not isinstance(llm_response, NonStreamingParsedLLMCallResponse):
                raise ValueError("LLM response is not of type NonStreamingParsedLLMCallResponse")

            return await self._get_response_from_parsed_llm_response(
                parsed_llm_response=llm_response.parsed_content,
                query_id=agent_chat_with_tool_call.query_id,
                session_id=payload.session_id,
                llm_model=LLModels(agent_chat_with_tool_call.metadata["llm_model"]),
            )

        if payload.query and payload.code_selection:
            # store in agent_chats
            generated_query_id = uuid4().hex
            code_selection = payload.code_selection
            agent_chat = await AgentChatsRepository.create_chat(
                chat_data=AgentChatCreateRequest(
                    session_id=payload.session_id,
                    actor=ActorType.USER,
                    message_type=MessageType.TEXT,
                    message_data=TextMessageData(
                        text=payload.query,
                        focus_items=[
                            CodeSnippetFocusItem(
                                chunks=[
                                    ChunkInfo(
                                        content=code_selection.selected_text,
                                        source_details=ChunkSourceDetails(
                                            file_path=code_selection.file_path,
                                            start_line=-1,
                                            end_line=-1,
                                        ),
                                    )
                                ],
                                path=code_selection.file_path,
                                # value as file name (taken from file path)
                                value=code_selection.file_path.split("/")[-1],
                            )
                        ],
                    ),
                    query_id=generated_query_id,
                    metadata={"is_inline_editor": True, "llm_model": LLModels(payload.llm_model.value)},
                    previous_queries=[],
                )
            )
            llm_response = await llm_handler.start_llm_query(
                prompt_feature=PromptFeatures.INLINE_EDITOR,
                llm_model=LLModels(payload.llm_model.value),
                prompt_vars={
                    "query": payload.query,
                    "code_selection": payload.code_selection,
                    "deputy_dev_rules": None,
                    "relevant_chunks": [],
                    "is_lsp_ready": payload.is_lsp_ready,
                    "repo_path": payload.repo_path,
                },
                previous_responses=[],
                tools=tools_to_use,
                tool_choice="required",
                stream=False,
                session_id=payload.session_id,
                conversation_turns=await self._get_conversation_turns_from_agent_chat_for_inline_edit(
                    agent_chats=[agent_chat], llm_model=LLModels(payload.llm_model.value), payload=payload
                ),
            )

            if not isinstance(llm_response, NonStreamingParsedLLMCallResponse):
                raise ValueError("LLM response is not of type NonStreamingParsedLLMCallResponse")

            return await self._get_response_from_parsed_llm_response(
                parsed_llm_response=llm_response.parsed_content,
                query_id=agent_chat.query_id,
                session_id=payload.session_id,
                llm_model=LLModels(payload.llm_model.value),
            )

        raise ValueError("Either query and code selection or tool use response must be provided")

    async def start_job(self, payload: InlineEditInput, job_id: int, client_data: ClientData) -> int:
        try:
            data = await self.get_inline_edit_diff_suggestion(payload=payload, client_data=client_data)
            await JobService.db_update(
                {
                    "id": job_id,
                },
                {
                    "status": "COMPLETED",
                    "final_output": data,
                },
            )
        except Exception as ex:  # noqa: BLE001
            await JobService.db_update(
                {
                    "id": job_id,
                },
                {
                    "status": "FAILED",
                    "final_output": {"error": str(ex)},
                },
            )

    async def create_and_start_job(self, payload: InlineEditInput, client_data: ClientData) -> int:
        job = await JobService.db_create(
            JobDTO(
                type="INLINE_EDIT",
                session_id=str(payload.session_id),
                user_team_id=payload.auth_data.user_team_id,
                status="PENDING",
            )
        )
        asyncio.create_task(self.start_job(payload, job_id=job.id, client_data=client_data))
        return job.id
