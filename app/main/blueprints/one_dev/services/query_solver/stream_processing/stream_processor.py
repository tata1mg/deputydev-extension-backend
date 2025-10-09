import asyncio
import json
from typing import AsyncIterator, List, Optional

from deputydev_core.llm_handler.core.handler import LLMHandler
from deputydev_core.llm_handler.dataclasses.main import (
    ParsedLLMCallResponse,
    StreamingEventType,
    StreamingParsedLLMCallResponse,
    TextBlockDelta,
    TextBlockEnd,
    TextBlockStart,
    ToolUseRequestDelta,
    ToolUseRequestEnd,
    ToolUseRequestStart,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels
from deputydev_core.utils.app_logger import AppLogger
from pydantic import BaseModel

from app.main.blueprints.one_dev.models.dto.agent_chats import (
    ActorType,
    AgentChatCreateRequest,
    CodeBlockData,
    MessageData,
    TextMessageData,
    ThinkingInfoData,
    ToolUseMessageData,
)
from app.main.blueprints.one_dev.models.dto.agent_chats import MessageType as ChatMessageType
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    Reasoning,
    ResponseMetadataBlock,
    ResponseMetadataContent,
    SessionSummaryBlock,
    TaskCompletionBlock,
    TaskCompletionContent,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.dataclasses.main import PromptFeatures
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.dataclasses.main import (
    CodeBlockDelta,
    CodeBlockEnd,
    CodeBlockStart,
    ThinkingBlockDelta,
    ThinkingBlockEnd,
    ThinkingBlockStart,
)
from app.main.blueprints.one_dev.services.query_solver.summary.summary_manager import SummaryManager
from app.main.blueprints.one_dev.services.repository.agent_chats.repository import AgentChatsRepository


class StreamProcessor:
    """Handle streaming operations for QuerySolver."""

    def __init__(self) -> None:
        self.summary_manager = SummaryManager()

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
        summary_task: Optional[asyncio.Task[str]] = None,
    ) -> AsyncIterator[BaseModel]:
        """Handle the final stream iterator with all message types."""
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
                content=ResponseMetadataContent(query_id=query_id, session_id=session_id),
                type="RESPONSE_METADATA",
            )

            if summary_task:

                async def _yield_summary() -> None:
                    try:
                        summary: str = await summary_task
                        if summary:
                            # This uses an asyncio.Queue to inject into the main generator
                            await queue.put(SessionSummaryBlock(content={"session_id": session_id, "summary": summary}))
                    except Exception as e:  # noqa: BLE001
                        AppLogger.log_error(f"Failed to generate session summary: {e}")

                queue: asyncio.Queue[BaseModel] = asyncio.Queue()
                asyncio.create_task(_yield_summary())
            else:
                queue = None

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
                if queue:
                    while not queue.empty():
                        yield await queue.get()

            # wait till the data has been stored in order to ensure that no race around occurs in submitting tool response
            await llm_response.llm_response_storage_task
            # Conditionally generate query summary only if no tool use was detected
            if not tool_use_detected:
                task = asyncio.create_task(
                    self.summary_manager.generate_query_summary(
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

                if queue and not queue.empty():
                    yield await queue.get()

        return _streaming_content_block_generator()
