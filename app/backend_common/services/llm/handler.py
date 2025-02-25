import asyncio
import json
import traceback
from typing import Dict, List, Optional, Union

import xxhash
from deputydev_core.utils.app_logger import AppLogger

from app.backend_common.models.dto.message_thread_dto import (
    LLModels,
    MessageDataTypes,
    MessageThreadActor,
    MessageThreadData,
    MessageThreadDTO,
    MessageType,
    ToolUseResponseMessageData,
)
from app.backend_common.repository.message_threads.repository import (
    MessageThreadsRepository,
)
from app.backend_common.services.llm.base_llm_provider import BaseLLMProvider
from app.backend_common.services.llm.dataclasses.main import (
    ContentBlockCategory,
    ConversationRole,
    ConversationTool,
    ConversationTurn,
    LLMCallResponseTypes,
    NonStreamingContentBlock,
    NonStreamingParsedLLMCallResponse,
    NonStreamingResponse,
    NonStreamingTextBlock,
    NonStreamingTextBlockContent,
    NonStreamingToolUseRequest,
    NonStreamingToolUseRequestContent,
    ParsedLLMCallResponse,
    PromptCacheConfig,
    StreamingEventType,
    StreamingParsedLLMCallResponse,
    StreamingResponse,
    UnparsedLLMCallResponse,
    UserAndSystemMessages,
)
from app.backend_common.services.llm.prompts.base_prompt import BasePrompt
from app.backend_common.services.llm.providers.anthropic.llm_provider import Anthropic
from app.backend_common.services.llm.providers.open_ai_reasioning_llm import (
    OpenAIReasoningLLM,
)
from app.backend_common.services.llm.providers.openai_llm import OpenaiLLM
from app.common.exception import RetryException


class LLMHandler:
    model_to_provider_class_map = {
        LLModels.CLAUDE_3_POINT_5_SONNET: Anthropic,
        LLModels.GPT_4O: OpenaiLLM,
        LLModels.GPT_40_MINI: OpenaiLLM,
        LLModels.GPT_O1_MINI: OpenAIReasoningLLM,
    }

    def __init__(
        self,
        prompt_handler_map: Dict[str, BasePrompt],
        cache_config: PromptCacheConfig = PromptCacheConfig(tools=False, system_message=False, conversation=False),
    ):
        self.prompt_handler_map = prompt_handler_map
        self.cache_config = cache_config

    async def get_non_streaming_response_from_streaming_response(
        self, llm_response: StreamingResponse
    ) -> NonStreamingResponse:
        non_streaming_content_blocks: List[NonStreamingContentBlock] = []

        current_content_block: Optional[NonStreamingContentBlock] = None
        text_buffer: str = ""

        async for event in llm_response.content:
            if event.type == StreamingEventType.TEXT_BLOCK_START:
                current_content_block = NonStreamingTextBlock(
                    type=ContentBlockCategory.TEXT_BLOCK, content=NonStreamingTextBlockContent(text="")
                )
            elif event.type == StreamingEventType.TEXT_BLOCK_DELTA:
                if current_content_block and isinstance(current_content_block, NonStreamingTextBlock):
                    current_content_block.content.text += event.content.text
            elif event.type == StreamingEventType.TEXT_BLOCK_END:
                if current_content_block and isinstance(current_content_block, NonStreamingTextBlock):
                    non_streaming_content_blocks.append(current_content_block)
                    current_content_block = None
            elif event.type == StreamingEventType.TOOL_USE_REQUEST_START:
                current_content_block = NonStreamingToolUseRequest(
                    type=ContentBlockCategory.TOOL_USE_REQUEST,
                    content=NonStreamingToolUseRequestContent(
                        tool_name=event.content.tool_name, tool_input={}, tool_use_id=event.content.tool_use_id
                    ),
                )
            elif event.type == StreamingEventType.TOOL_USE_REQUEST_DELTA:
                if current_content_block and isinstance(current_content_block, NonStreamingToolUseRequest):
                    text_buffer += event.content.input_params_json_delta
            elif event.type == StreamingEventType.TOOL_USE_REQUEST_END:
                if current_content_block and isinstance(current_content_block, NonStreamingToolUseRequest):
                    current_content_block.content.tool_input = json.loads(text_buffer)
                    non_streaming_content_blocks.append(current_content_block)
                    current_content_block = None
                    text_buffer = ""

        return NonStreamingResponse(
            type=LLMCallResponseTypes.NON_STREAMING,
            content=non_streaming_content_blocks,
            usage=await llm_response.usage,
        )

    async def store_llm_response_in_db(
        self, llm_response: UnparsedLLMCallResponse, session_id: int, prompt_handler: BasePrompt
    ) -> None:
        response_to_use: NonStreamingResponse
        if llm_response.type == LLMCallResponseTypes.STREAMING:
            response_to_use = await self.get_non_streaming_response_from_streaming_response(llm_response)
        else:
            response_to_use = llm_response

        response_to_use.content.sort(key=lambda x: x.type.value)
        data_to_store: List[NonStreamingContentBlock] = response_to_use.content
        data_hash = xxhash.xxh64(json.dumps([data.model_dump(mode="json") for data in data_to_store])).hexdigest()
        message_thread = MessageThreadData(
            session_id=session_id,
            actor=MessageThreadActor.ASSISTANT,
            query_id=None,
            message_type=MessageType.RESPONSE,
            conversation_chain=[],
            message_data=data_to_store,
            data_hash=data_hash,
            llm_model=prompt_handler.model_name,
            prompt_type=prompt_handler.prompt_type,
            usage=response_to_use.usage,
        )
        await MessageThreadsRepository.create_message_thread(message_thread)

    async def get_llm_response(
        self,
        client: BaseLLMProvider,
        model: LLModels,
        session_id: int,
        prompt_handler: BasePrompt,
        prompt: Optional[UserAndSystemMessages] = None,
        tools: Optional[List[ConversationTool]] = None,
        tool_use_response: Optional[ToolUseResponseMessageData] = None,
        previous_responses: List[MessageThreadDTO] = [],
        max_retry: int = 2,
        stream: bool = False,
    ) -> UnparsedLLMCallResponse:
        for i in range(0, max_retry):
            try:
                llm_payload = client.build_llm_payload(
                    prompt=prompt,
                    tool_use_response=tool_use_response,
                    previous_responses=previous_responses,
                    tools=tools,
                    cache_config=self.cache_config,
                )
                llm_response = await client.call_service_client(llm_payload, model, stream=stream)
                # start task for storing LLM message in DB
                asyncio.create_task(self.store_llm_response_in_db(llm_response, session_id, prompt_handler))
                return llm_response
            except Exception as e:
                AppLogger.log_debug(traceback.format_exc())
                print(traceback.format_exc())
                AppLogger.log_warn(f"Retry {i + 1}/{max_retry}  Error while fetching data from LLM: {e}")
                await asyncio.sleep(2)
        raise RetryException(f"Failed to get response from LLM after {max_retry} retries")

    async def parse_llm_response_data(
        self, llm_response: UnparsedLLMCallResponse, prompt_handler: BasePrompt
    ) -> ParsedLLMCallResponse:
        if llm_response.type == LLMCallResponseTypes.STREAMING:
            parsed_stream = await prompt_handler.get_parsed_streaming_events(llm_response)
            return StreamingParsedLLMCallResponse(
                type=llm_response.type,
                content=llm_response.content,
                parsed_content=parsed_stream,
                usage=llm_response.usage,
                model_used=prompt_handler.model_name,
                prompt_vars={},
                prompt_id=prompt_handler.prompt_type,
            )
        else:
            parsed_content = prompt_handler.get_parsed_result(llm_response)
            return NonStreamingParsedLLMCallResponse(
                type=llm_response.type,
                content=llm_response.content,
                parsed_content=parsed_content,
                usage=llm_response.usage,
                model_used=prompt_handler.model_name,
                prompt_vars={},
                prompt_id=prompt_handler.prompt_type,
            )

    async def fetch_message_threads_from_conversation_turns(
        self, conversation_turns: List[ConversationTurn], session_id: int
    ) -> List[MessageThreadDTO]:
        """
        Fetch message threads from conversation turns

        Parameters:
            :param conversation_turns: List of conversation turns

        Returns:
            :return: List of message threads
        """
        hashes_to_fetch: List[str] = []
        for turn in conversation_turns:
            if turn.content:
                hashes_to_fetch.append(xxhash.xxh64(str(turn.content)).hexdigest())

        db_message_threads = await MessageThreadsRepository.get_message_threads_for_session(session_id=session_id)
        db_message_threads_hash_map: Dict[str, MessageThreadDTO] = {
            message.data_hash: message for message in db_message_threads
        }

        message_threads_to_insert: List[MessageThreadData] = []
        for turn, hash in zip(conversation_turns, hashes_to_fetch):
            if hash not in db_message_threads_hash_map:
                message_thread = MessageThreadData(
                    session_id=session_id,
                    actor=MessageThreadActor.USER
                    if turn.role == ConversationRole.USER
                    else MessageThreadActor.ASSISTANT,
                    query_id=None,
                    message_type=MessageType.RESPONSE,
                    conversation_chain=[],
                    data_hash=hash,
                    message_data=[],
                    prompt_type="",
                    llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
                    summary=None,
                )
                message_threads_to_insert.append(message_thread)

        recently_inserted_message_threads_map: Dict[str, MessageThreadDTO] = {}
        if message_threads_to_insert:
            inserted_message_threads = await MessageThreadsRepository.bulk_insert_message_threads(
                message_threads_to_insert
            )
            recently_inserted_message_threads_map: Dict[str, MessageThreadDTO] = {
                message.data_hash: message for message in inserted_message_threads
            }

        final_message_threads: List[MessageThreadDTO] = []
        for hash in hashes_to_fetch:
            final_message_threads.append(
                recently_inserted_message_threads_map[hash]
                if hash in recently_inserted_message_threads_map
                else db_message_threads_hash_map[hash]
            )

        return final_message_threads

    async def get_message_threads_from_message_thread_ids(
        self, message_thread_ids: List[int]
    ) -> List[MessageThreadDTO]:
        """
        Get message threads from message thread ids
        """

        if not message_thread_ids:
            return []

        db_message_threads = await MessageThreadsRepository.get_message_threads_by_ids(
            message_thread_ids=message_thread_ids
        )
        return db_message_threads

    async def get_conversation_chain_messages(
        self, session_id: int, previous_responses: Union[List[int], List[ConversationTurn]] = []
    ) -> List[MessageThreadDTO]:
        """
        Get conversation chain messages

        Parameters:
            :param session_id: Session id
            :param previous_responses: List of previous conversation messages (can be list of conversation turn or list of message ids)

        Returns:
            :return: List of conversation messages
        """
        # return empty list if no previous responses
        if not previous_responses:
            return []

        # determine the type of previous_responses
        if isinstance(previous_responses[0], ConversationTurn):
            return await self.fetch_message_threads_from_conversation_turns(
                conversation_turns=previous_responses, session_id=session_id
            )
        return await self.get_message_threads_from_message_thread_ids(message_thread_ids=previous_responses)

    async def start_llm_query(
        self,
        session_id: int,
        prompt_handler: BasePrompt,
        tools: Optional[List[ConversationTool]] = None,
        previous_responses: Union[List[int], List[ConversationTurn]] = [],
        stream: bool = False,
    ) -> ParsedLLMCallResponse:
        """
        Start LLM query

        Parameters:
            :param prompt_handler: Prompt handler
            :param tools: List of tools
            :param previous_responses: List of previous conversation messages (can be list of conversation turn or list of message ids)
            :param stream: Stream response

        Returns:
            :return: Parsed LLM response
        """
        detected_llm = prompt_handler.model_name

        if detected_llm not in self.model_to_provider_class_map:
            raise ValueError(f"LLM model {detected_llm} not supported")

        client = self.model_to_provider_class_map[detected_llm]()
        prompt = prompt_handler.get_prompt()

        llm_response = await self.get_llm_response(
            client=client,
            prompt=prompt,
            tools=tools,
            model=detected_llm,
            previous_responses=await self.get_conversation_chain_messages(
                session_id=session_id, previous_responses=previous_responses
            ),
            stream=stream,
        )

        return await self.parse_llm_response_data(llm_response=llm_response, prompt_handler=prompt_handler)

    async def generate_previous_messages(self, session_messages: List[MessageThreadDTO]) -> List[ConversationTurn]:
        """
        Generate previous messages from session messages

        Parameters:
            :param session_messages: List of session messages

        Returns:
            :return: List of conversation turns
        """
        previous_messages: List[ConversationTurn] = []
        for message in session_messages:
            for data in message.message_data:
                if data.type == MessageDataTypes.TEXT:
                    previous_messages.append(
                        ConversationTurn(
                            role=ConversationRole.USER
                            if message.actor == MessageThreadActor.USER
                            else ConversationRole.ASSISTANT,
                            content=data.text,
                        )
                    )
                elif data.type == MessageDataTypes.TOOL_USE_REQUEST:
                    previous_messages.append(
                        ConversationTurn(
                            role=ConversationRole.USER
                            if message.actor == MessageThreadActor.USER
                            else ConversationRole.ASSISTANT,
                            content=data.tool_name,
                        )
                    )
                elif data.type == MessageDataTypes.TOOL_USE_RESPONSE:
                    previous_messages.append(
                        ConversationTurn(
                            role=ConversationRole.USER
                            if message.actor == MessageThreadActor.USER
                            else ConversationRole.ASSISTANT,
                            content=str(data.response),
                        )
                    )
        return previous_messages

    async def submit_tool_use_response(
        self,
        session_id: str,
        tool_use_response: ToolUseResponseMessageData,
        tools: Optional[List[ConversationTool]] = None,
        stream: bool = False,
    ) -> ParsedLLMCallResponse:
        """
        Submit tool use response to LLM

        Parameters:
            :param session_id: Session id
            :param tool_use_response: Tool use response data
            :param tools: List of tools
            :param stream: Stream response
            :return: Parsed LLM response

        Returns:
            ParsedLLMCallResponse: Parsed LLM response
        """

        session_messages = await MessageThreadsRepository.get_message_threads_for_session(session_id=session_id)
        filtered_messages = [message for message in session_messages if message.message_type == MessageType.RESPONSE]

        detected_llm: Optional[LLModels] = None
        tool_use_request_message_id = None
        detected_prompt_handler: Optional[BasePrompt] = None
        for message in filtered_messages:
            for data in message.message_data:
                if data.type == MessageDataTypes.TOOL_USE_REQUEST and data.tool_use_id == tool_use_response.tool_use_id:
                    tool_use_request_message_id = message.id
                    detected_llm = message.llm_model
                    detected_prompt_handler = self.prompt_handler_map.get(message.prompt_type)
                    break

        if not tool_use_request_message_id or not detected_llm:
            raise ValueError(
                f"Tool use request message not found for tool use response id {tool_use_response.tool_use_id}"
            )

        if not detected_prompt_handler:
            raise ValueError("Prompt handler not found for prompt type")

        client = self.model_to_provider_class_map[detected_llm]()
        llm_response = await self.get_llm_response(
            client=client,
            tool_use_response=tool_use_response,
            tools=tools,
            model=detected_llm,
            previous_responses=[message for message in session_messages if message.id <= tool_use_request_message_id],
            stream=stream,
        )

        return await self.parse_llm_response_data(llm_response=llm_response, prompt_handler=detected_prompt_handler)
