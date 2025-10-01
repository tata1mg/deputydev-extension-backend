import asyncio
import json
from typing import Any, AsyncIterator, Dict, List, Optional, Union
from uuid import uuid4

from deputydev_core.llm_handler.core.handler import LLMHandler
from deputydev_core.llm_handler.dataclasses.main import (
    NonStreamingParsedLLMCallResponse,
    ParsedLLMCallResponse,
    PromptCacheConfig,
    StreamingEventType,
    StreamingParsedLLMCallResponse,
    TextBlockDelta,
    TextBlockEnd,
    TextBlockStart,
    ToolUseRequestDelta,
    ToolUseRequestEnd,
    ToolUseRequestStart,
)
from deputydev_core.llm_handler.dataclasses.unified_conversation_turn import (
    AssistantConversationTurn,
    ToolConversationTurn,
    UnifiedConversationTurn,
    UnifiedTextConversationTurnContent,
    UnifiedToolRequestConversationTurnContent,
    UnifiedToolResponseConversationTurnContent,
    UserConversationTurn,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import (
    LLModels,
    MessageCallChainCategory,
    MessageThreadDTO,
    MessageType,
)
from deputydev_core.services.chunking.chunk_info import ChunkInfo
from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.config_manager import ConfigManager
from pydantic import BaseModel
from sanic.server.websockets.impl import WebsocketImplProtocol

from app.backend_common.caches.code_gen_tasks_cache import CodeGenTasksCache
from app.backend_common.models.dto.extension_sessions_dto import ExtensionSessionData
from app.backend_common.repository.chat_attachments.repository import ChatAttachmentsRepository
from app.backend_common.services.chat_file_upload.chat_file_upload import ChatFileUpload
from app.backend_common.services.llm.llm_service_manager import LLMServiceManager
from app.backend_common.utils.dataclasses.main import AuthData, ClientData
from app.backend_common.utils.tool_response_parser import LLMResponseFormatter
from app.main.blueprints.one_dev.constants.tools import ToolStatus
from app.main.blueprints.one_dev.models.dto.agent_chats import (
    ActorType,
    AgentChatCreateRequest,
    AgentChatDTO,
    AgentChatUpdateRequest,
    CodeBlockData,
    InfoMessageData,
    MessageData,
    TextMessageData,
    ThinkingInfoData,
    ToolUseMessageData,
)
from app.main.blueprints.one_dev.models.dto.agent_chats import MessageType as ChatMessageType
from app.main.blueprints.one_dev.models.dto.query_summaries import QuerySummaryData
from app.main.blueprints.one_dev.services.query_solver.agent.query_solver_agent import QuerySolverAgent
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    FocusItem,
    LLMModel,
    QuerySolverInput,
    Reasoning,
    ResponseMetadataBlock,
    ResponseMetadataContent,
    RetryReasons,
    TaskCompletionBlock,
    TaskCompletionContent,
    ToolUseResponseInput,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.dataclasses.main import (
    CodeBlockDelta,
    CodeBlockEnd,
    CodeBlockStart,
    ThinkingBlockDelta,
    ThinkingBlockEnd,
    ThinkingBlockStart,
)
from app.main.blueprints.one_dev.services.repository.agent_chats.repository import AgentChatsRepository
from app.main.blueprints.one_dev.services.repository.query_solver_agents.repository import QuerySolverAgentsRepository
from app.main.blueprints.one_dev.services.repository.query_summaries.query_summary_dto import (
    QuerySummarysRepository,
)
from app.main.blueprints.one_dev.utils.cancellation_checker import (
    CancellationChecker,
)

from .agent_selector.agent_selector import QuerySolverAgentSelector
from .prompts.factory import PromptFeatureFactory
from .stream_handler.stream_handler import StreamHandler


class QuerySolver:
    @staticmethod
    async def start_pinger(ws: WebsocketImplProtocol, interval: int = 25) -> None:
        """Start a background pinger task to keep WebSocket connection alive."""
        try:
            while True:
                await asyncio.sleep(interval)
                try:
                    await ws.send(json.dumps({"type": "PING"}))
                except Exception:  # noqa: BLE001
                    break  # stop pinging if connection breaks
        except asyncio.CancelledError:
            pass

    @staticmethod
    async def process_s3_payload(payload_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Process S3 attachment payload and return the processed payload."""
        attachment_id = payload_dict["attachment_id"]
        attachment_data = await ChatAttachmentsRepository.get_attachment_by_id(attachment_id=attachment_id)
        if not attachment_data or getattr(attachment_data, "status", None) == "deleted":
            raise ValueError(f"Attachment with ID {attachment_id} not found or already deleted.")

        s3_key = attachment_data.s3_key
        try:
            object_bytes = await ChatFileUpload.get_file_data_by_s3_key(s3_key=s3_key)
            s3_payload = json.loads(object_bytes.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise ValueError(f"Failed to decode JSON payload from S3: {e}")

        # Preserve important fields from original payload
        for field in ("session_id", "session_type", "auth_token"):
            if field in payload_dict:
                s3_payload[field] = payload_dict[field]

        # Cleanup S3 resources
        try:
            await ChatFileUpload.delete_file_by_s3_key(s3_key=s3_key)
        except Exception:  # noqa: BLE001
            AppLogger.log_error(f"Failed to delete S3 file {s3_key}")

        try:
            await ChatAttachmentsRepository.update_attachment_status(attachment_id, "deleted")
        except Exception:  # noqa: BLE001
            AppLogger.log_error(f"Failed to update status for attachment {attachment_id}")

        return s3_payload

    @staticmethod
    async def handle_session_data_caching(payload: QuerySolverInput) -> None:
        """Handle session data caching for the payload."""
        await CodeGenTasksCache.cleanup_session_data(payload.session_id)

        session_data_dict = {}
        if payload.query:
            session_data_dict["query"] = payload.query
            if payload.llm_model:
                session_data_dict["llm_model"] = payload.llm_model.value
            await CodeGenTasksCache.set_session_data(payload.session_id, session_data_dict)

    async def execute_query_processing(
        self,
        payload: Union[QuerySolverInput, QuerySolverResumeInput],
        client_data: ClientData,
        auth_data: AuthData,
        ws: WebsocketImplProtocol,
    ) -> None:
        """Execute the query processing and stream results."""
        task_checker = CancellationChecker(payload.session_id)
        try:
            await task_checker.start_monitoring()

            # Send stream start notification
            start_data = {"type": "STREAM_START"}
            if auth_data.session_refresh_token:
                start_data["new_session_data"] = auth_data.session_refresh_token
            await ws.send(json.dumps(start_data))

            # Handle different payload types
            if self._is_resume_payload(payload):
                # Resume case: get existing query_id and start from offset
                query_id = await self.start_query_solver(
                    payload=payload, client_data=client_data, task_checker=task_checker
                )
                # Get stream from specific offset if provided
                offset_id = payload.resume_offset_id or "0"
                stream_iterator = await self.get_stream(query_id, offset_id=offset_id)
            else:
                # Normal case: start new query processing
                query_id = await self.start_query_solver(
                    payload=payload, client_data=client_data, task_checker=task_checker
                )
                stream_iterator = await self.get_stream(query_id)

            # Stream events to client
            async for data_block in stream_iterator:
                event_data = data_block.model_dump(mode="json")
                await ws.send(json.dumps(event_data))

                # Handle session cleanup for specific events
                if event_data.get("type") == "QUERY_COMPLETE":
                    await CodeGenTasksCache.cleanup_session_data(payload.session_id)

        except Exception as ex:  # noqa: BLE001
            AppLogger.log_error(f"Error in WebSocket solve_query: {ex}")
            await ws.send(json.dumps({"type": "STREAM_ERROR", "message": f"WebSocket error: {str(ex)}"}))
        finally:
            await task_checker.stop_monitoring()

    async def _generate_session_summary(
        self,
        session_id: int,
        query: str,
        focus_items: List[FocusItem],
        llm_handler: LLMHandler[PromptFeatures],
        user_team_id: int,
        session_type: str,
    ) -> None:
        current_session = await ExtensionSessionsRepository.find_or_create(session_id, user_team_id, session_type)
        if current_session and current_session.summary:
            return

        # if no summary, first generate a summary by directly putting first 100 characters of the query.
        # this will be used as a placeholder until the LLM generates a more detailed summary.
        brief_query_preview = query[:100]
        await ExtensionSessionsRepository.update_session_summary(
            session_id=session_id, summary=f"{brief_query_preview}..."
        )

        # then generate a more detailed summary using LLM
        llm_response = await llm_handler.start_llm_query(
            prompt_feature=PromptFeatures.SESSION_SUMMARY_GENERATOR,
            llm_model=LLModels.GEMINI_2_POINT_5_FLASH,
            prompt_vars={"query": query, "focus_items": focus_items},
            previous_responses=[],
            tools=[],
            stream=False,
            session_id=session_id,
            call_chain_category=MessageCallChainCategory.SYSTEM_CHAIN,
        )

        if not isinstance(llm_response, NonStreamingParsedLLMCallResponse):
            raise ValueError("Expected NonStreamingParsedLLMCallResponse")

        generated_summary = llm_response.parsed_content[0].get("summary")
        await ExtensionSessionsRepository.update_session_summary(session_id=session_id, summary=generated_summary)

    def _format_tool_response(
        self, tool_response: ToolUseResponseInput, vscode_env: Optional[str], focus_items: Optional[List[FocusItem]]
    ) -> Dict[str, Any]:
        """Handle and structure tool responses based on tool type."""

        if tool_response.status != ToolStatus.COMPLETED:
            return tool_response.response if tool_response.response else {}

        if tool_response.tool_name == "focused_snippets_searcher":
            return {
                "chunks": [
                    ChunkInfo(**chunk).get_xml()
                    for search_response in tool_response.response["batch_chunks_search"]["response"]
                    for chunk in search_response["chunks"]
                ],
            }

        if tool_response.tool_name == "iterative_file_reader":
            markdown = LLMResponseFormatter.format_iterative_file_reader_response(tool_response.response["data"])
            return {"Tool Response": markdown}

        if tool_response.tool_name == "grep_search":
            markdown = LLMResponseFormatter.format_grep_tool_response(tool_response.response)
            return {"Tool Response": markdown}

        if tool_response.tool_name == "ask_user_input":
            json_response = LLMResponseFormatter.format_ask_user_input_response(
                tool_response.response, vscode_env, focus_items
            )
            return json_response

        return tool_response.response if tool_response.response else {}

    async def _store_tool_response_in_chat_chain(
        self,
        tool_response: ToolUseResponseInput,
        session_id: int,
        vscode_env: Optional[str],
        focus_items: Optional[List[FocusItem]],
    ) -> AgentChatDTO:
        # store query in DB
        tool_use_chats = await AgentChatsRepository.get_chats_by_message_type_and_session(
            message_type=ChatMessageType.TOOL_USE, session_id=session_id
        )
        selected_tool_use_chat = next(
            (
                chat
                for chat in tool_use_chats
                if getattr(chat.message_data, "tool_use_id", None) == tool_response.tool_use_id
            ),
            None,
        )

        if not selected_tool_use_chat or not isinstance(selected_tool_use_chat.message_data, ToolUseMessageData):
            raise Exception("tool use request not found")

        formatted_response_data = self._format_tool_response(tool_response, vscode_env, focus_items)
        updated_chat = await AgentChatsRepository.update_chat(
            chat_id=selected_tool_use_chat.id,
            update_data=AgentChatUpdateRequest(
                message_data=ToolUseMessageData(
                    tool_use_id=selected_tool_use_chat.message_data.tool_use_id,
                    tool_response=formatted_response_data,
                    tool_name=selected_tool_use_chat.message_data.tool_name,
                    tool_input=selected_tool_use_chat.message_data.tool_input,
                    tool_status=tool_response.status,
                )
            ),
        )
        if not updated_chat:
            raise Exception("Failed to update tool use chat with response")
        return updated_chat

    async def _get_conversation_turns_for_summary(
        self, agent_chats: List[AgentChatDTO]
    ) -> List[UnifiedConversationTurn]:
        conv_turns_for_summarization: List[UnifiedConversationTurn] = []

        for chat in agent_chats:
            if chat.actor == ActorType.USER:
                conv_turns_for_summarization.append(
                    UserConversationTurn(
                        content=[
                            UnifiedTextConversationTurnContent(
                                text=chat.message_data.text if isinstance(chat.message_data, TextMessageData) else ""
                            )
                        ]
                    )
                )
            elif chat.actor == ActorType.ASSISTANT:
                if chat.message_type == ChatMessageType.TEXT and isinstance(chat.message_data, TextMessageData):
                    conv_turns_for_summarization.append(
                        AssistantConversationTurn(
                            content=[UnifiedTextConversationTurnContent(text=chat.message_data.text)]
                        )
                    )
                elif chat.message_type == ChatMessageType.CODE_BLOCK and isinstance(chat.message_data, CodeBlockData):
                    code_content = f"```{chat.message_data.language}\n{chat.message_data.code}\n```"
                    if chat.message_data.file_path:
                        code_content = f"File: {chat.message_data.file_path}\n" + code_content
                    conv_turns_for_summarization.append(
                        AssistantConversationTurn(content=[UnifiedTextConversationTurnContent(text=code_content)])
                    )
                elif chat.message_type == ChatMessageType.TOOL_USE and isinstance(
                    chat.message_data, ToolUseMessageData
                ):
                    conv_turns_for_summarization.append(
                        AssistantConversationTurn(
                            content=[
                                UnifiedToolRequestConversationTurnContent(
                                    tool_name=chat.message_data.tool_name,
                                    tool_input=chat.message_data.tool_input,
                                    tool_use_id=chat.message_data.tool_use_id,
                                )
                            ]
                        )
                    )
                    if chat.message_data.tool_response:
                        conv_turns_for_summarization.append(
                            ToolConversationTurn(
                                content=[
                                    UnifiedToolResponseConversationTurnContent(
                                        tool_name=chat.message_data.tool_name,
                                        tool_use_response=chat.message_data.tool_response,
                                        tool_use_id=chat.message_data.tool_use_id,
                                    )
                                ]
                            )
                        )
                    else:
                        conv_turns_for_summarization.append(
                            ToolConversationTurn(
                                content=[
                                    UnifiedToolResponseConversationTurnContent(
                                        tool_name=chat.message_data.tool_name,
                                        tool_use_response={"result": "NO RESULT"},
                                        tool_use_id=chat.message_data.tool_use_id,
                                    )
                                ]
                            )
                        )

        prompt_handler = PromptFeatureFactory.get_prompt(
            model_name=LLModels.GPT_4_POINT_1_NANO,
            feature=PromptFeatures.QUERY_SUMMARY_GENERATOR,
        )(params={})
        user_and_system_message = prompt_handler.get_prompt()
        conv_turns_for_summarization.append(
            UserConversationTurn(
                content=[UnifiedTextConversationTurnContent(text=user_and_system_message.user_message)]
            )
        )

        return conv_turns_for_summarization

    async def _generate_query_summary(
        self,
        session_id: int,
        query_id: str,
        llm_handler: LLMHandler[PromptFeatures],
    ) -> tuple[Optional[str], bool]:  # Always return a tuple
        all_messages = await AgentChatsRepository.get_chats_by_session_id(session_id=session_id)
        # filter messages to be from current query only
        filtered_agent_chats = [chat for chat in all_messages if chat.query_id == query_id]
        filtered_agent_chats.sort(key=lambda x: x.created_at)

        conv_turns = await self._get_conversation_turns_for_summary(filtered_agent_chats)

        # then generate a more detailed summary using LLM
        llm_response = await llm_handler.start_llm_query(
            prompt_feature=PromptFeatures.QUERY_SUMMARY_GENERATOR,
            llm_model=LLModels.GPT_4_POINT_1_NANO,
            prompt_vars={},
            tools=[],
            stream=False,
            session_id=session_id,
            call_chain_category=MessageCallChainCategory.SYSTEM_CHAIN,
            conversation_turns=conv_turns,
        )

        if not isinstance(llm_response, NonStreamingParsedLLMCallResponse):
            raise ValueError("Expected NonStreamingParsedLLMCallResponse")
        query_summary = llm_response.parsed_content[0].summary or ""
        query_status = (
            llm_response.parsed_content[0].success if hasattr(llm_response.parsed_content[0], "success") else True
        )

        _summary_updation_task = asyncio.create_task(self._update_query_summary(query_id, query_summary, session_id))
        return query_summary, query_status

    async def _update_query_summary(self, query_id: str, summary: str, session_id: int) -> None:
        existing_summary = await QuerySummarysRepository.get_query_summary(session_id=session_id, query_id=query_id)
        if existing_summary:
            new_updated_summary = existing_summary.summary + "\n" + summary
            await QuerySummarysRepository.update_query_summary(
                session_id=session_id, query_id=query_id, summary=new_updated_summary
            )
        else:
            await QuerySummarysRepository.create_query_summary(
                QuerySummaryData(
                    session_id=session_id,
                    query_id=query_id,
                    summary=summary,
                )
            )

    async def get_final_stream_iterator(  # noqa: C901
        self,
        llm_response: ParsedLLMCallResponse,
        session_id: int,
        llm_handler: LLMHandler[PromptFeatures],
        query_id: str,
        previous_queries: List[str],
        llm_model: LLModels,
        agent_name: str,
        reasoning: Optional[Reasoning],
    ) -> AsyncIterator[BaseModel]:
        query_summary: Optional[str] = None
        tool_use_detected: bool = False

        async def _update_current_message_data_for_text(
            current_message_data: Optional[TextMessageData],
            event: TextBlockStart | TextBlockDelta | TextBlockEnd,
            previous_queries: List[str],
        ) -> Optional[MessageData]:
            new_data: Optional[MessageData] = None
            if isinstance(event, TextBlockStart):
                new_data = TextMessageData(text="")
            elif isinstance(event, TextBlockDelta):
                new_data = TextMessageData(
                    text=((current_message_data.text if current_message_data else "") + event.content.text)
                )
            elif current_message_data:  # TextBlockEnd
                await AgentChatsRepository.create_chat(
                    chat_data=AgentChatCreateRequest(
                        session_id=session_id,
                        actor=ActorType.ASSISTANT,
                        message_data=current_message_data,
                        message_type=ChatMessageType.TEXT,
                        metadata={
                            "llm_model": llm_model.value,
                            "agent_name": agent_name,
                            **({"reasoning": reasoning.value} if reasoning else {}),
                        },
                        query_id=query_id,
                        previous_queries=previous_queries,
                    )
                )
                new_data = None

            return new_data

        async def _update_current_message_data_for_thinking(
            current_message_data: Optional[ThinkingInfoData],
            event: ThinkingBlockStart | ThinkingBlockDelta | ThinkingBlockEnd,
            previous_queries: List[str],
        ) -> Optional[MessageData]:
            new_data: Optional[MessageData] = None
            if isinstance(event, ThinkingBlockStart):
                new_data = ThinkingInfoData(
                    thinking_summary="",
                    ignore_in_chat=getattr(event, "ignore_in_chat", False),
                )
            elif isinstance(event, ThinkingBlockDelta):
                new_data = ThinkingInfoData(
                    thinking_summary=(
                        (current_message_data.thinking_summary if current_message_data else "")
                        + event.content.thinking_delta
                    ),
                    ignore_in_chat=getattr(event, "ignore_in_chat", False)
                    if hasattr(event, "ignore_in_chat")
                    else (current_message_data.ignore_in_chat if current_message_data else False),
                )
            elif current_message_data:  # ThinkingBlockEnd
                await AgentChatsRepository.create_chat(
                    chat_data=AgentChatCreateRequest(
                        session_id=session_id,
                        actor=ActorType.ASSISTANT,
                        message_data=current_message_data,
                        message_type=ChatMessageType.THINKING,
                        metadata={
                            "llm_model": llm_model.value,
                            "agent_name": agent_name,
                            **({"reasoning": reasoning.value} if reasoning else {}),
                        },
                        query_id=query_id,
                        previous_queries=previous_queries,
                    )
                )
                new_data = None

            return new_data

        async def _update_current_message_data_for_code(
            current_message_data: Optional[CodeBlockData],
            event: CodeBlockStart | CodeBlockDelta | CodeBlockEnd,
            previous_queries: List[str],
        ) -> Optional[MessageData]:
            new_data: Optional[MessageData] = None
            if isinstance(event, CodeBlockStart):
                new_data = CodeBlockData(language=event.content.language, file_path=event.content.filepath, code="")
            elif isinstance(event, CodeBlockDelta):
                if current_message_data:
                    new_data = CodeBlockData(
                        language=current_message_data.language,
                        file_path=current_message_data.file_path,
                        code=current_message_data.code + event.content.code_delta,
                    )
            elif current_message_data:  # CodeBlockEnd
                await AgentChatsRepository.create_chat(
                    chat_data=AgentChatCreateRequest(
                        session_id=session_id,
                        actor=ActorType.ASSISTANT,
                        message_data=CodeBlockData(
                            language=current_message_data.language,
                            file_path=current_message_data.file_path,
                            code=current_message_data.code,
                            diff=event.content.diff,
                        ),
                        message_type=ChatMessageType.CODE_BLOCK,
                        metadata={
                            "llm_model": llm_model.value,
                            "agent_name": agent_name,
                            **({"reasoning": reasoning.value} if reasoning else {}),
                        },
                        query_id=query_id,
                        previous_queries=previous_queries,
                    )
                )
                new_data = None

            return new_data

        async def _update_current_message_data_for_tool_use(
            current_message_data: Optional[ToolUseMessageData],
            event: ToolUseRequestStart | ToolUseRequestDelta | ToolUseRequestEnd,
            previous_queries: List[str],
        ) -> Optional[MessageData]:
            new_data: Optional[MessageData] = None
            if isinstance(event, ToolUseRequestStart):
                new_data = ToolUseMessageData(
                    tool_name=event.content.tool_name,
                    tool_input={},
                    tool_use_id=event.content.tool_use_id,
                )
            elif isinstance(event, ToolUseRequestDelta):
                if current_message_data:
                    new_data = ToolUseMessageData(
                        tool_name=current_message_data.tool_name,
                        tool_input={
                            "delta": current_message_data.tool_input.get("delta", "")
                            + event.content.input_params_json_delta
                        },
                        tool_use_id=current_message_data.tool_use_id,
                    )
            elif current_message_data:  # ToolUseRequestEnd
                await AgentChatsRepository.create_chat(
                    chat_data=AgentChatCreateRequest(
                        session_id=session_id,
                        actor=ActorType.ASSISTANT,
                        message_data=ToolUseMessageData(
                            tool_name=current_message_data.tool_name,
                            tool_input=json.loads(current_message_data.tool_input.get("delta", "{}")),
                            tool_use_id=current_message_data.tool_use_id,
                        ),
                        message_type=ChatMessageType.TOOL_USE,
                        metadata={
                            "llm_model": llm_model.value,
                            "agent_name": agent_name,
                            **({"reasoning": reasoning.value} if reasoning else {}),
                        },
                        query_id=query_id,
                        previous_queries=previous_queries,
                    )
                )
                new_data = None

            return new_data

        async def _streaming_content_block_generator() -> AsyncIterator[BaseModel]:  # noqa: C901
            nonlocal llm_response
            nonlocal query_summary
            nonlocal tool_use_detected
            if not isinstance(llm_response, StreamingParsedLLMCallResponse):
                raise ValueError("Expected StreamingParsedLLMCallResponse")

            yield ResponseMetadataBlock(
                content=ResponseMetadataContent(query_id=llm_response.query_id, session_id=session_id),
                type="RESPONSE_METADATA",
            )

            current_message_data: Optional[MessageData] = None

            async for data_block in llm_response.parsed_content:
                # Check if the current task is cancelled
                current_task = asyncio.current_task()
                if current_task and current_task.cancelled():
                    raise asyncio.CancelledError("Task cancelled in QuerySolver")

                if data_block.type in [
                    StreamingEventType.TOOL_USE_REQUEST_START,
                    StreamingEventType.TOOL_USE_REQUEST_DELTA,
                    StreamingEventType.TOOL_USE_REQUEST_END,
                    StreamingEventType.MALFORMED_TOOL_USE_REQUEST,
                ]:
                    tool_use_detected = True

                if (
                    isinstance(data_block, TextBlockStart)
                    or isinstance(data_block, TextBlockDelta)
                    or isinstance(data_block, TextBlockEnd)
                ):
                    current_message_data = await _update_current_message_data_for_text(
                        current_message_data, data_block, previous_queries
                    )

                elif (
                    isinstance(data_block, ThinkingBlockStart)
                    or isinstance(data_block, ThinkingBlockDelta)
                    or isinstance(data_block, ThinkingBlockEnd)
                ):
                    current_message_data = await _update_current_message_data_for_thinking(
                        current_message_data, data_block, previous_queries
                    )

                elif (
                    isinstance(data_block, CodeBlockStart)
                    or isinstance(data_block, CodeBlockDelta)
                    or isinstance(data_block, CodeBlockEnd)
                ):
                    current_message_data = await _update_current_message_data_for_code(
                        current_message_data, data_block, previous_queries
                    )

                elif (
                    isinstance(data_block, ToolUseRequestStart)
                    or isinstance(data_block, ToolUseRequestDelta)
                    or isinstance(data_block, ToolUseRequestEnd)
                ):
                    current_message_data = await _update_current_message_data_for_tool_use(
                        current_message_data, data_block, previous_queries
                    )

                yield data_block

            # wait till the data has been stored in order to ensure that no race around occurs in submitting tool response
            await llm_response.llm_response_storage_task
            # Conditionally generate query summary only if no tool use was detected
            if not tool_use_detected:
                task = asyncio.create_task(
                    self._generate_query_summary(
                        session_id=session_id,
                        query_id=query_id,
                        llm_handler=llm_handler,
                    )
                )
                done, _pending = await asyncio.wait([task], timeout=5.0)

                if task in done:
                    query_summary, success = task.result()
                else:
                    AppLogger.log_info(f"Query summary generation timed out after 5 seconds, Query id: {query_id}")
                    query_summary = None
                    success = True

                yield TaskCompletionBlock(
                    content=TaskCompletionContent(
                        query_id=llm_response.query_id,
                        success=success,
                        summary=query_summary,
                    ),
                    type="TASK_COMPLETION",
                )

        return _streaming_content_block_generator()

    async def _generate_dynamic_query_solver_agents(self) -> List[QuerySolverAgent]:
        # get all the intents from the database
        default_agent = QuerySolverAgent(
            agent_name="DEFAULT_QUERY_SOLVER_AGENT",
            agent_description="This is the default query solver agent that should used when no specific agent is solves the purpose",
        )
        all_agents = await QuerySolverAgentsRepository.get_query_solver_agents()
        if not all_agents:
            return [default_agent]

        # create a list of agent classes based on the data from the database
        agent_classes: List[QuerySolverAgent] = []
        for agent_data in all_agents:
            agent_class = QuerySolverAgent(
                agent_name=agent_data.name,
                agent_description=agent_data.description,
                allowed_tools=agent_data.allowed_first_party_tools,
                prompt_intent=agent_data.prompt_intent,
            )
            agent_classes.append(agent_class)

        return agent_classes + [default_agent]

    async def _get_last_query_message_for_session(self, session_id: int) -> Optional[MessageThreadDTO]:
        """
        Get the last query message for the session.
        """
        try:
            messages = await MessageThreadsRepository.get_message_threads_for_session(
                session_id, call_chain_category=MessageCallChainCategory.CLIENT_CHAIN
            )
            last_query_message = None
            for message in messages:
                if message.message_type == MessageType.QUERY and message.prompt_type in [
                    "CODE_QUERY_SOLVER",
                    "CODE_QUERY_SOLVER",
                ]:
                    last_query_message = message
            return last_query_message
        except Exception as ex:  # noqa: BLE001
            AppLogger.log_error(f"Error occurred while fetching last query message for session {session_id}: {ex}")
            return None

    def _get_agent_instance_by_name(self, agent_name: str, all_agents: List[QuerySolverAgent]) -> QuerySolverAgent:
        """
        Get the agent instance by its name.
        """
        agent = next((agent for agent in all_agents if agent.agent_name == agent_name), None)
        if not agent:
            raise ValueError(f"Agent with name {agent_name} not found")
        return agent

    async def _get_query_solver_agent_instance(
        self,
        payload: QuerySolverInput,
        llm_handler: LLMHandler[PromptFeatures],
        previous_agent_chats: List[AgentChatDTO],
    ) -> QuerySolverAgent:
        all_agents = await self._generate_dynamic_query_solver_agents()  # this will have default agent as well
        agent_instance: QuerySolverAgent

        if not all_agents:
            raise Exception("No query solver agents found in the system")

        if payload.query:
            agent_selector = QuerySolverAgentSelector(
                user_query=payload.query,
                focus_items=payload.focus_items,
                last_agent=previous_agent_chats[-1].metadata.get("agent_name")
                if previous_agent_chats and previous_agent_chats[-1].metadata
                else None,
                all_agents=all_agents,
                llm_handler=llm_handler,
                session_id=payload.session_id,
            )

            agent_instance = await agent_selector.select_agent()
        else:
            agent_name = (
                previous_agent_chats[-1].metadata.get("agent_name")
                if previous_agent_chats and previous_agent_chats[-1].metadata
                else None
            )
            agent_instance: QuerySolverAgent = self._get_agent_instance_by_name(
                agent_name=agent_name or "DEFAULT_QUERY_SOLVER_AGENT",
                all_agents=all_agents,
            )
        return agent_instance

    def _get_model_change_text(
        self, current_model: LLModels, new_model: LLModels, retry_reason: Optional[RetryReasons]
    ) -> str:
        """Return a human-readable explanation of why the LLM model was changed."""

        def get_model_display_name(model_name: str) -> str:
            """Get the display name for a model from the configuration."""
            chat_models = ConfigManager.configs.get("CODE_GEN_LLM_MODELS", [])
            for model in chat_models:
                if model.get("name") == model_name:
                    return model.get("display_name", model_name)
            return model_name

        current_display = get_model_display_name(current_model.value)
        new_display = get_model_display_name(new_model.value)

        if retry_reason == RetryReasons.TOOL_USE_FAILED:
            return f"LLM model changed from {current_display} to {new_display} due to tool use failure."
        elif retry_reason == RetryReasons.THROTTLED:
            return f"LLM model changed from {current_display} to {new_display} due to throttling."
        elif retry_reason == RetryReasons.TOKEN_LIMIT_EXCEEDED:
            return f"LLM model changed from {current_display} to {new_display} due to token limit exceeded."
        else:
            return f"LLM model changed from {current_display} to {new_display} by the user."

    async def _set_required_model(
        self,
        llm_model: LLModels,
        session_id: int,
        query_id: str,
        agent_name: str,
        retry_reason: Optional[RetryReasons],
        user_team_id: int,
        session_type: str,
        reasoning: Optional[Reasoning],
    ) -> None:
        """
        Set the required model for the session.
        """
        current_session = await ExtensionSessionsRepository.get_by_id(session_id=session_id)

        if not current_session:
            current_session = await ExtensionSessionsRepository.create_extension_session(
                extension_session_data=ExtensionSessionData(
                    session_id=session_id,
                    user_team_id=user_team_id,
                    session_type=session_type,
                    current_model=llm_model,
                )
            )

        if current_session.current_model != llm_model:
            # TODO: remove after v15 Force upgrade
            if (
                llm_model == LLModels.OPENROUTER_GPT_4_POINT_1
                and current_session.current_model == LLModels.GPT_4_POINT_1
            ):
                await asyncio.gather(
                    ExtensionSessionsRepository.update_session_llm_model(session_id=session_id, llm_model=llm_model),
                )
                return  # no need to store a message in chat as the models are equivalent

            # update current model in session
            await asyncio.gather(
                ExtensionSessionsRepository.update_session_llm_model(session_id=session_id, llm_model=llm_model),
                AgentChatsRepository.create_chat(
                    chat_data=AgentChatCreateRequest(
                        session_id=session_id,
                        actor=ActorType.SYSTEM,
                        message_data=InfoMessageData(
                            info=self._get_model_change_text(
                                current_model=LLModels(current_session.current_model),
                                new_model=llm_model,
                                retry_reason=retry_reason,
                            )
                        ),
                        message_type=ChatMessageType.INFO,
                        metadata={
                            "llm_model": llm_model.value,
                            "agent_name": agent_name,
                            **({"reasoning": reasoning.value} if reasoning else {}),
                        },
                        query_id=query_id,
                        previous_queries=[],
                    )
                ),
            )

    async def solve_query(
        self,
        payload: QuerySolverInput,
        client_data: ClientData,
        save_to_redis: bool = False,
        task_checker: Optional[CancellationChecker] = None,
    ) -> AsyncIterator[BaseModel]:
        llm_handler = LLMServiceManager().create_llm_handler(
            prompt_factory=PromptFeatureFactory,
            prompt_features=PromptFeatures,
            cache_config=PromptCacheConfig(conversation=True, tools=True, system_message=True),
        )

        reasoning = Reasoning(payload.reasoning) if payload.reasoning else None

        # TODO: remove after v15 Force upgrade
        if payload.llm_model and LLMModel(payload.llm_model.value) == LLMModel.GPT_4_POINT_1:
            payload.llm_model = LLMModel.OPENROUTER_GPT_4_POINT_1

        if payload.query:
            # get current model and check if it is changed, if yes, store a note in chat
            generated_query_id = uuid4().hex

            if not payload.llm_model:
                raise ValueError("LLM model is required for query solving.")

            session_chats = await AgentChatsRepository.get_chats_by_session_id(session_id=payload.session_id)
            session_chats.sort(key=lambda x: x.created_at)

            agent_instance = await self._get_query_solver_agent_instance(
                payload=payload, llm_handler=llm_handler, previous_agent_chats=session_chats
            )

            await self._set_required_model(
                llm_model=LLModels(payload.llm_model.value),
                session_id=payload.session_id,
                query_id=generated_query_id,
                agent_name=agent_instance.agent_name,
                retry_reason=payload.retry_reason,
                user_team_id=payload.user_team_id,
                session_type=payload.session_type,
                reasoning=reasoning,
            )

            new_query_chat = await AgentChatsRepository.create_chat(
                chat_data=AgentChatCreateRequest(
                    session_id=payload.session_id,
                    actor=ActorType.USER,
                    message_data=TextMessageData(
                        text=payload.query,
                        attachments=payload.attachments,
                        focus_items=payload.focus_items,
                        vscode_env=payload.vscode_env,
                        repositories=payload.repositories,
                    ),
                    message_type=ChatMessageType.TEXT,
                    metadata={
                        "llm_model": LLModels(payload.llm_model.value).value,
                        "agent_name": agent_instance.agent_name,
                    },
                    query_id=generated_query_id,
                    previous_queries=[],
                )
            )

            _summary_task = asyncio.create_task(
                self._generate_session_summary(
                    session_id=payload.session_id,
                    query=payload.query,
                    focus_items=payload.focus_items,
                    llm_handler=llm_handler,
                    user_team_id=payload.user_team_id,
                    session_type=payload.session_type,
                )
            )

            prompt_vars_to_use: Dict[str, Any] = {
                "query": payload.query,
                "focus_items": payload.focus_items,
                "deputy_dev_rules": payload.deputy_dev_rules,
                "write_mode": payload.write_mode,
                "os_name": payload.os_name,
                "shell": payload.shell,
                "vscode_env": payload.vscode_env,
                "repositories": payload.repositories,
            }

            model_to_use = LLModels(payload.llm_model.value)
            llm_inputs, previous_queries = await agent_instance.get_llm_inputs_and_previous_queries(
                payload=payload, _client_data=client_data, llm_model=model_to_use, new_query_chat=new_query_chat
            )

            prompt_vars_to_use = {**prompt_vars_to_use, **llm_inputs.extra_prompt_vars}

            llm_response = await llm_handler.start_llm_query(
                prompt_feature=PromptFeatures(llm_inputs.prompt.prompt_type),
                llm_model=model_to_use,
                reasoning=reasoning,
                prompt_vars=prompt_vars_to_use,
                attachments=payload.attachments,
                conversation_turns=llm_inputs.messages,
                tools=llm_inputs.tools,
                stream=True,
                session_id=payload.session_id,
                save_to_redis=save_to_redis,
                checker=task_checker,
                parallel_tool_calls=True,
                prompt_handler_instance=llm_inputs.prompt(params=prompt_vars_to_use),
                metadata={
                    "agent_name": agent_instance.agent_name,
                    **({"reasoning": reasoning.value} if reasoning else {}),
                },
            )
            return await self.get_final_stream_iterator(
                llm_response,
                session_id=payload.session_id,
                llm_handler=llm_handler,
                query_id=generated_query_id,
                previous_queries=previous_queries,
                llm_model=model_to_use,
                agent_name=agent_instance.agent_name,
                reasoning=reasoning,
            )

        elif payload.batch_tool_responses:
            inserted_tool_responses = await asyncio.gather(
                *[
                    self._store_tool_response_in_chat_chain(
                        tool_resp, payload.session_id, payload.vscode_env, payload.focus_items
                    )
                    for tool_resp in payload.batch_tool_responses
                ]
            )

            prompt_vars: Dict[str, Any] = {
                "os_name": payload.os_name,
                "shell": payload.shell,
                "vscode_env": payload.vscode_env,
                "write_mode": payload.write_mode,
                "deputy_dev_rules": payload.deputy_dev_rules,
            }

            agent_instance = await self._get_query_solver_agent_instance(
                payload=payload, llm_handler=llm_handler, previous_agent_chats=inserted_tool_responses
            )
            llm_to_use = LLModels(inserted_tool_responses[0].metadata["llm_model"])
            reasoning_val = inserted_tool_responses[0].metadata.get("reasoning")
            reasoning = Reasoning(reasoning_val) if reasoning_val else None
            if payload.retry_reason is not None:
                llm_to_use = LLModels(payload.llm_model.value)
                reasoning = Reasoning(payload.reasoning) if payload.reasoning else None

            await self._set_required_model(
                llm_model=llm_to_use,
                session_id=payload.session_id,
                query_id=inserted_tool_responses[0].query_id,
                agent_name=agent_instance.agent_name,
                retry_reason=payload.retry_reason,
                user_team_id=payload.user_team_id,
                session_type=payload.session_type,
                reasoning=reasoning,
            )

            llm_inputs, previous_queries = await agent_instance.get_llm_inputs_and_previous_queries(
                payload=payload,
                _client_data=client_data,
                llm_model=llm_to_use,
            )
            prompt_vars_to_use = {**prompt_vars, **llm_inputs.extra_prompt_vars}
            llm_response = await llm_handler.start_llm_query(
                session_id=payload.session_id,
                tools=llm_inputs.tools,
                stream=True,
                prompt_vars=prompt_vars_to_use,
                checker=task_checker,
                parallel_tool_calls=True,
                prompt_feature=PromptFeatures(llm_inputs.prompt.prompt_type),
                llm_model=llm_to_use,
                reasoning=reasoning,
                conversation_turns=llm_inputs.messages,
            )

            return await self.get_final_stream_iterator(
                llm_response,
                session_id=payload.session_id,
                llm_handler=llm_handler,
                query_id=inserted_tool_responses[0].query_id,
                previous_queries=previous_queries,
                llm_model=llm_to_use,
                agent_name=agent_instance.agent_name,
                reasoning=reasoning,
            )

        else:
            raise ValueError("Invalid input")

    async def start_query_solver(
        self,
        payload: QuerySolverInput,
        client_data: ClientData,
        task_checker: Optional[CancellationChecker] = None,
    ) -> str:
        """
        Wrapper function that starts the query solver and handles streaming part.
        Returns the query_id which is used as stream_id for getting the stream.

        Args:
            payload: QuerySolverInput containing the query and parameters
            client_data: Client data for the request
            task_checker: Optional cancellation checker

        Returns:
            str: The query_id (used as stream_id) to retrieve the stream
        """
        # Check if this is a resume payload
        if self._is_resume_payload(payload):
            return await self.resume_stream(payload)

        # Normal payload - generate new query_id and start processing
        query_id = uuid4().hex

        # Start the query solving process in background
        asyncio.create_task(
            self._solve_query_with_streaming(
                payload=payload,
                client_data=client_data,
                query_id=query_id,
                task_checker=task_checker,
            )
        )

        return query_id

    async def get_stream(self, query_id: str, offset_id: str = "0") -> AsyncIterator[BaseModel]:
        """
        Get the stream iterator from Redis stream using query_id as stream_id.

        Args:
            query_id: The query ID (used as stream_id) to retrieve the stream
            offset_id: The offset ID to start reading from (defaults to "0")

        Returns:
            AsyncIterator[BaseModel]: Async iterator for stream events
        """
        async for event in StreamHandler.stream_from(stream_id=query_id, offset_id=offset_id):
            yield event

    async def resume_stream(
        self,
        payload: QuerySolverInput,
    ) -> str:
        """
        Resume an existing stream from a given checkpoint ID and query_id.
        This will continue streaming from the specified offset without running the query solver again.

        Args:
            payload: QuerySolverInput containing the resume_query_id and resume_offset_id

        Returns:
            str: The same query_id that was being resumed

        Raises:
            ValueError: If resume_query_id is not provided
        """
        if not payload.resume_query_id:
            raise ValueError("resume_query_id is required for resuming a stream")

        # Return the same query_id for stream continuation
        return payload.resume_query_id

    def _is_s3_payload(self, payload_dict: Dict[str, Any]) -> bool:
        """
        Check if the payload is from S3 (has attachment_id).

        Args:
            payload_dict: Raw payload dictionary

        Returns:
            bool: True if this is an S3 payload, False otherwise
        """
        return payload_dict.get("type") == "PAYLOAD_ATTACHMENT" and payload_dict.get("attachment_id") is not None

    def _is_resume_payload(self, payload: Union[QuerySolverInput, QuerySolverResumeInput]) -> bool:
        """
        Check if the payload is for resuming a stream.

        Args:
            payload: QuerySolverInput or QuerySolverResumeInput to check

        Returns:
            bool: True if this is a resume payload, False otherwise
        """
        return isinstance(payload, QuerySolverResumeInput)

    def _is_normal_payload(self, payload: Union[QuerySolverInput, QuerySolverResumeInput]) -> bool:
        """
        Check if the payload is a normal query payload.

        Args:
            payload: QuerySolverInput or QuerySolverResumeInput to check

        Returns:
            bool: True if this is a normal payload, False otherwise
        """
        return isinstance(payload, QuerySolverInput) and not isinstance(payload, QuerySolverResumeInput)

    async def _solve_query_with_streaming(
        self,
        payload: QuerySolverInput,
        client_data: ClientData,
        query_id: str,
        task_checker: Optional[CancellationChecker] = None,
    ) -> None:
        """
        Internal method that handles the actual query solving with error handling
        and streams results to Redis.

        Args:
            payload: QuerySolverInput containing the query and parameters
            client_data: Client data for the request
            query_id: The query ID to use as stream_id
            task_checker: Optional cancellation checker
        """
        from deputydev_core.exceptions.exceptions import InputTokenLimitExceededError
        from deputydev_core.exceptions.llm_exceptions import LLMThrottledError

        try:
            # Get the stream iterator from the existing solve_query method
            stream_iterator = await self.solve_query(
                payload=payload,
                client_data=client_data,
                save_to_redis=True,
                task_checker=task_checker,
            )

            # Stream all events to Redis using StreamHandler
            last_event = None
            async for event in stream_iterator:
                last_event = event
                await StreamHandler.push_to_stream(stream_id=query_id, data=event)

            # Push completion events
            if (
                last_event
                and hasattr(last_event, "type")
                and last_event.type != StreamingEventType.TOOL_USE_REQUEST_END
            ):
                completion_event = self._create_completion_event()
                await StreamHandler.push_to_stream(stream_id=query_id, data=completion_event)

                close_event = self._create_close_event()
                await StreamHandler.push_to_stream(stream_id=query_id, data=close_event)
            else:
                end_event = self._create_end_event()
                await StreamHandler.push_to_stream(stream_id=query_id, data=end_event)

        except LLMThrottledError as ex:
            AppLogger.log_error(f"LLM throttled error in query solver: {ex}")
            error_event = self._create_llm_throttled_error_event(ex)
            await StreamHandler.push_to_stream(stream_id=query_id, data=error_event)

        except InputTokenLimitExceededError as ex:
            AppLogger.log_error(
                f"Input token limit exceeded: model={ex.model_name}, tokens={ex.current_tokens}/{ex.max_tokens}"
            )
            error_event = await self._create_token_limit_error_event(ex, payload.query)
            await StreamHandler.push_to_stream(stream_id=query_id, data=error_event)

        except asyncio.CancelledError as ex:
            AppLogger.log_error(f"Query cancelled: {ex}")
            error_event = self._create_error_event(f"LLM processing error: {str(ex)}")
            await StreamHandler.push_to_stream(stream_id=query_id, data=error_event)

        except Exception as e:
            # Handle other errors by pushing error event to stream
            AppLogger.log_error(f"Error in query solver: {e}")
            error_event = self._create_error_event(f"LLM processing error: {str(e)}")
            await StreamHandler.push_to_stream(stream_id=query_id, data=error_event)

    def _create_error_event(self, error_message: str) -> BaseModel:
        """
        Create an error event BaseModel for streaming.

        Args:
            error_message: The error message to include

        Returns:
            BaseModel: Error event model
        """

        class StreamErrorEvent(BaseModel):
            type: str = "STREAM_ERROR"
            message: str

        return StreamErrorEvent(message=error_message)

    def _create_llm_throttled_error_event(self, ex) -> BaseModel:
        """
        Create a throttled error event BaseModel for streaming.

        Args:
            ex: LLMThrottledError exception

        Returns:
            BaseModel: Throttled error event model
        """

        class LLMThrottledErrorEvent(BaseModel):
            type: str = "STREAM_ERROR"
            status: str = "LLM_THROTTLED"
            provider: Optional[str] = None
            model: Optional[str] = None
            retry_after: Optional[int] = None
            message: str = "This chat is currently being throttled. You can wait, or switch to a different model."
            detail: Optional[str] = None
            region: Optional[str] = None

        return LLMThrottledErrorEvent(
            provider=getattr(ex, "provider", None),
            model=getattr(ex, "model", None),
            retry_after=ex.retry_after,
            detail=ex.detail,
            region=getattr(ex, "region", None),
        )

    async def _create_token_limit_error_event(self, ex, query: str) -> BaseModel:
        """
        Create a token limit exceeded error event BaseModel for streaming.

        Args:
            ex: InputTokenLimitExceededError exception
            query: The original query

        Returns:
            BaseModel: Token limit error event model
        """
        from typing import Any, Dict, List

        # Get available models with higher token limits
        better_models: List[Dict[str, Any]] = []

        try:
            code_gen_models = ConfigManager.configs.get("CODE_GEN_LLM_MODELS", [])
            llm_models_config = ConfigManager.configs.get("LLM_MODELS", {})
            current_model_limit = ex.max_tokens

            for model in code_gen_models:
                model_name = model.get("name")
                if model_name and model_name != ex.model_name and model_name in llm_models_config:
                    model_config = llm_models_config[model_name]
                    model_token_limit = model_config.get("INPUT_TOKENS_LIMIT", 100000)

                    if model_token_limit > current_model_limit:
                        enhanced_model = model.copy()
                        enhanced_model["input_token_limit"] = model_token_limit
                        better_models.append(enhanced_model)

            # Sort by token limit (highest first)
            better_models.sort(key=lambda m: m.get("input_token_limit", 0), reverse=True)

        except Exception as model_error:
            AppLogger.log_error(f"Error fetching better models: {model_error}")

        def get_model_display_name(model_name: str) -> str:
            """Get the display name for a model from the configuration."""
            try:
                chat_models = ConfigManager.configs.get("CODE_GEN_LLM_MODELS", [])
                for model in chat_models:
                    if model.get("name") == model_name:
                        return model.get("display_name", model_name)
                return model_name
            except Exception:
                return model_name

        class TokenLimitErrorEvent(BaseModel):
            type: str = "STREAM_ERROR"
            status: str = "INPUT_TOKEN_LIMIT_EXCEEDED"
            model: str
            current_tokens: int
            max_tokens: int
            query: str
            message: str
            detail: Optional[str]
            better_models: List[Dict[str, Any]]

        return TokenLimitErrorEvent(
            model=ex.model_name,
            current_tokens=ex.current_tokens,
            max_tokens=ex.max_tokens,
            query=query,
            message=f"Your message exceeds the context window supported by {get_model_display_name(ex.model_name)}. Try switching to a model with a higher context window to proceed.",
            detail=ex.detail,
            better_models=better_models,
        )

    def _create_completion_event(self) -> BaseModel:
        """Create a query completion event BaseModel for streaming."""

        class QueryCompletionEvent(BaseModel):
            type: str = "QUERY_COMPLETE"

        return QueryCompletionEvent()

    def _create_close_event(self) -> BaseModel:
        """Create a stream end close connection event BaseModel for streaming."""

        class StreamEndCloseEvent(BaseModel):
            type: str = "STREAM_END_CLOSE_CONNECTION"

        return StreamEndCloseEvent()

    def _create_end_event(self) -> BaseModel:
        """Create a stream end event BaseModel for streaming."""

        class StreamEndEvent(BaseModel):
            type: str = "STREAM_END"

        return StreamEndEvent()
