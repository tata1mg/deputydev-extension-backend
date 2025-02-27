import asyncio
import json
import traceback
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, Sequence, Type, TypeVar, Union

import xxhash
from deputydev_core.utils.app_logger import AppLogger

from app.backend_common.models.dto.message_thread_dto import (
    ContentBlockCategory,
    LLModels,
    MessageCallChainCategory,
    MessageThreadActor,
    MessageThreadData,
    MessageThreadDTO,
    MessageType,
    ResponseData,
    TextBlockContent,
    TextBlockData,
    ToolUseRequestContent,
    ToolUseRequestData,
    ToolUseResponseData,
)
from app.backend_common.repository.message_threads.repository import (
    MessageThreadsRepository,
)
from app.backend_common.services.llm.base_llm_provider import BaseLLMProvider
from app.backend_common.services.llm.dataclasses.main import (
    ConversationRole,
    ConversationTool,
    ConversationTurn,
    LLMCallResponseTypes,
    NonStreamingParsedLLMCallResponse,
    NonStreamingResponse,
    ParsedLLMCallResponse,
    PromptCacheConfig,
    StreamingEventType,
    StreamingParsedLLMCallResponse,
    StreamingResponse,
    UnparsedLLMCallResponse,
    UserAndSystemMessages,
)
from app.backend_common.services.llm.prompts.base_prompt import BasePrompt
from app.backend_common.services.llm.prompts.base_prompt_feature_factory import (
    BasePromptFeatureFactory,
)
from app.backend_common.services.llm.providers.anthropic.llm_provider import Anthropic
from app.backend_common.services.llm.providers.open_ai_reasioning_llm import (
    OpenAIReasoningLLM,
)
from app.backend_common.services.llm.providers.openai_llm import OpenaiLLM
from app.common.exception import RetryException

PromptFeatures = TypeVar("PromptFeatures", bound=Enum)


class LLMHandler(Generic[PromptFeatures]):
    model_to_provider_class_map = {
        LLModels.CLAUDE_3_POINT_5_SONNET: Anthropic,
        LLModels.GPT_4O: OpenaiLLM,
        LLModels.GPT_40_MINI: OpenaiLLM,
        LLModels.GPT_O1_MINI: OpenAIReasoningLLM,
    }

    def __init__(
        self,
        prompt_factory: Type[BasePromptFeatureFactory[PromptFeatures]],
        prompt_features: Type[PromptFeatures],
        cache_config: PromptCacheConfig = PromptCacheConfig(tools=False, system_message=False, conversation=False),
    ):
        self.prompt_handler_map = prompt_factory
        self.prompt_features = prompt_features
        self.cache_config = cache_config

    async def get_non_streaming_response_from_streaming_response(
        self, llm_response: StreamingResponse
    ) -> NonStreamingResponse:
        non_streaming_content_blocks: List[ResponseData] = []

        current_content_block: Optional[ResponseData] = None
        text_buffer: str = ""

        for event in await llm_response.accumulated_events:
            if event.type == StreamingEventType.TEXT_BLOCK_START:
                current_content_block = TextBlockData(
                    type=ContentBlockCategory.TEXT_BLOCK, content=TextBlockContent(text="")
                )
            elif event.type == StreamingEventType.TEXT_BLOCK_DELTA:
                if current_content_block and isinstance(current_content_block, TextBlockData):
                    current_content_block.content.text += event.content.text
            elif event.type == StreamingEventType.TEXT_BLOCK_END:
                if current_content_block and isinstance(current_content_block, TextBlockData):
                    non_streaming_content_blocks.append(current_content_block)
                    current_content_block = None
            elif event.type == StreamingEventType.TOOL_USE_REQUEST_START:
                current_content_block = ToolUseRequestData(
                    type=ContentBlockCategory.TOOL_USE_REQUEST,
                    content=ToolUseRequestContent(
                        tool_name=event.content.tool_name, tool_input={}, tool_use_id=event.content.tool_use_id
                    ),
                )
            elif event.type == StreamingEventType.TOOL_USE_REQUEST_DELTA:
                if current_content_block and isinstance(current_content_block, ToolUseRequestData):
                    text_buffer += event.content.input_params_json_delta
            elif event.type == StreamingEventType.TOOL_USE_REQUEST_END:
                if current_content_block and isinstance(current_content_block, ToolUseRequestData):
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
        self,
        llm_response: UnparsedLLMCallResponse,
        session_id: int,
        prompt_type: str,
        llm_model: LLModels,
        query_id: int,
        call_chain_category: MessageCallChainCategory,
    ) -> None:
        print("storing task started ********************************************************")
        response_to_use: NonStreamingResponse
        if llm_response.type == LLMCallResponseTypes.STREAMING:
            response_to_use = await self.get_non_streaming_response_from_streaming_response(llm_response)
        else:
            response_to_use = llm_response

        print("response to use generated *********************************************************")
        response_to_use.content.sort(key=lambda x: x.type.value)
        data_to_store: Sequence[ResponseData] = response_to_use.content
        data_hash = xxhash.xxh64(json.dumps([data.model_dump(mode="json") for data in data_to_store])).hexdigest()
        message_thread = MessageThreadData(
            session_id=session_id,
            actor=MessageThreadActor.ASSISTANT,
            query_id=query_id,
            message_type=MessageType.RESPONSE,
            conversation_chain=[],
            message_data=data_to_store,
            data_hash=data_hash,
            llm_model=llm_model,
            prompt_type=prompt_type,
            usage=response_to_use.usage,
            call_chain_category=call_chain_category,
        )
        print("response data *********************************************************")
        print(message_thread)
        await MessageThreadsRepository.create_message_thread(message_thread)
        print("HHBDKJDHODIE")

    async def store_llm_query_in_db(
        self,
        session_id: int,
        previous_responses: List[MessageThreadDTO],
        prompt_type: str,
        llm_model: LLModels,
        prompt_rendered_messages: UserAndSystemMessages,
        prompt_vars: Dict[str, Any],
        call_chain_category: MessageCallChainCategory,
    ) -> MessageThreadDTO:
        """
        Store LLM query in DB

        Parameters:
            :param prompt: User and system messages
            :param session_id: Session id
            :param previous_responses: List of previous conversation messages

        Returns:
            :return: Message thread
        """
        data_hash = xxhash.xxh64(prompt_rendered_messages.user_message).hexdigest()
        message_thread = MessageThreadData(
            session_id=session_id,
            actor=MessageThreadActor.USER,
            query_id=None,
            message_type=MessageType.QUERY,
            conversation_chain=[message.id for message in previous_responses],
            message_data=[
                TextBlockData(
                    type=ContentBlockCategory.TEXT_BLOCK,
                    content=TextBlockContent(text=prompt_rendered_messages.user_message),
                )
            ],
            data_hash=data_hash,
            prompt_type=prompt_type,
            llm_model=llm_model,
            query_vars=prompt_vars,
            call_chain_category=call_chain_category,
        )
        return await MessageThreadsRepository.create_message_thread(message_thread)

    async def get_llm_response(
        self,
        client: BaseLLMProvider,
        session_id: int,
        prompt_type: str,
        llm_model: LLModels,
        query_id: int,
        call_chain_category: MessageCallChainCategory,
        tools: Optional[List[ConversationTool]] = None,
        user_and_system_messages: Optional[UserAndSystemMessages] = None,
        tool_use_response: Optional[ToolUseResponseData] = None,
        previous_responses: List[MessageThreadDTO] = [],
        max_retry: int = 2,
        stream: bool = False,
    ) -> UnparsedLLMCallResponse:
        for i in range(0, max_retry):
            try:
                llm_payload = client.build_llm_payload(
                    prompt=user_and_system_messages,
                    tool_use_response=tool_use_response,
                    previous_responses=previous_responses,
                    tools=tools,
                    cache_config=self.cache_config,
                )
                llm_response = await client.call_service_client(llm_payload, llm_model, stream=stream)
                # start task for storing LLM message in DB
                print("storing task started ********************************************************")
                asyncio.create_task(
                    self.store_llm_response_in_db(
                        llm_response,
                        session_id,
                        prompt_type=prompt_type,
                        llm_model=llm_model,
                        query_id=query_id,
                        call_chain_category=call_chain_category,
                    )
                )
                print("storing task started ********************************************************")
                return llm_response
            except Exception as e:
                AppLogger.log_debug(traceback.format_exc())
                print(traceback.format_exc())
                AppLogger.log_warn(f"Retry {i + 1}/{max_retry}  Error while fetching data from LLM: {e}")
                await asyncio.sleep(2)
        raise RetryException(f"Failed to get response from LLM after {max_retry} retries")

    async def parse_llm_response_data(
        self, llm_response: UnparsedLLMCallResponse, prompt_handler: BasePrompt, query_id: int
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
                accumulated_events=llm_response.accumulated_events,
                query_id=query_id,
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
                query_id=query_id,
            )

    async def fetch_message_threads_from_conversation_turns(
        self,
        conversation_turns: List[ConversationTurn],
        session_id: int,
        prompt_handler: BasePrompt,
        call_chain_category: MessageCallChainCategory,
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

        db_message_threads = await MessageThreadsRepository.get_message_threads_for_session(
            session_id=session_id, call_chain_category=call_chain_category
        )
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
                    prompt_type=prompt_handler.prompt_type,
                    llm_model=prompt_handler.model_name,
                    call_chain_category=call_chain_category,
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
        self,
        session_id: int,
        call_chain_category: MessageCallChainCategory,
        prompt_handler: BasePrompt,
        previous_responses: Union[List[int], List[ConversationTurn]] = [],
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
                conversation_turns=previous_responses,
                session_id=session_id,
                prompt_handler=prompt_handler,
                call_chain_category=call_chain_category,
            )
        data = await self.get_message_threads_from_message_thread_ids(message_thread_ids=previous_responses)
        data.sort(key=lambda x: x.id)
        return data

    async def start_llm_query(
        self,
        session_id: int,
        prompt_feature: PromptFeatures,
        llm_model: LLModels,
        prompt_vars: Dict[str, Any],
        tools: Optional[List[ConversationTool]] = None,
        previous_responses: Union[List[int], List[ConversationTurn]] = [],
        stream: bool = False,
        call_chain_category: MessageCallChainCategory = MessageCallChainCategory.CLIENT_CHAIN,
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

        prompt_handler = self.prompt_handler_map.get_prompt(model_name=llm_model, feature=prompt_feature)(prompt_vars)

        if llm_model not in self.model_to_provider_class_map:
            raise ValueError(f"LLM model {llm_model} not supported")

        client = self.model_to_provider_class_map[llm_model]()
        user_and_system_messages = prompt_handler.get_prompt()

        conversation_chain_messages = await self.get_conversation_chain_messages(
            session_id=session_id,
            previous_responses=previous_responses,
            prompt_handler=prompt_handler,
            call_chain_category=call_chain_category,
        )

        prompt_thread = await self.store_llm_query_in_db(
            session_id=session_id,
            previous_responses=conversation_chain_messages,
            prompt_type=prompt_handler.prompt_type,
            llm_model=prompt_handler.model_name,
            prompt_rendered_messages=user_and_system_messages,
            prompt_vars=prompt_vars,
            call_chain_category=call_chain_category,
        )

        llm_response = await self.get_llm_response(
            user_and_system_messages=user_and_system_messages,
            client=client,
            prompt_type=prompt_handler.prompt_type,
            llm_model=prompt_handler.model_name,
            session_id=session_id,
            tools=tools,
            previous_responses=conversation_chain_messages,
            stream=stream,
            query_id=prompt_thread.id,
            call_chain_category=call_chain_category,
        )

        return await self.parse_llm_response_data(
            llm_response=llm_response, prompt_handler=prompt_handler, query_id=prompt_thread.id
        )

    async def store_tool_use_ressponse_in_db(
        self,
        session_id: int,
        tool_use_response: ToolUseResponseData,
        prompt_type: str,
        llm_model: LLModels,
        previous_responses: List[MessageThreadDTO],
        query_id: int,
        call_chain_category: MessageCallChainCategory,
    ) -> MessageThreadDTO:
        """
        Store tool use response in DB
        """
        message_data = [tool_use_response]
        data_hash = xxhash.xxh64(json.dumps([item.model_dump(mode="json") for item in message_data])).hexdigest()
        message_thread = MessageThreadData(
            session_id=session_id,
            actor=MessageThreadActor.USER,
            query_id=query_id,
            message_type=MessageType.TOOL_RESPONSE,
            conversation_chain=[message.id for message in previous_responses],
            message_data=message_data,
            data_hash=data_hash,
            prompt_type=prompt_type,
            llm_model=llm_model,
            call_chain_category=call_chain_category,
        )
        return await MessageThreadsRepository.create_message_thread(message_thread)

    async def submit_tool_use_response(
        self,
        session_id: int,
        tool_use_response: ToolUseResponseData,
        tools: Optional[List[ConversationTool]] = None,
        stream: bool = False,
        call_chain_category: MessageCallChainCategory = MessageCallChainCategory.CLIENT_CHAIN,
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

        session_messages = await MessageThreadsRepository.get_message_threads_for_session(
            session_id=session_id, call_chain_category=call_chain_category
        )
        filtered_messages = [message for message in session_messages if message.message_type == MessageType.RESPONSE]

        detected_llm: Optional[LLModels] = None
        tool_use_request_message_id = None
        detected_prompt_handler: Optional[BasePrompt] = None
        main_query_id: int = 0
        for message in filtered_messages:
            for data in message.message_data:
                if (
                    data.type == ContentBlockCategory.TOOL_USE_REQUEST
                    and data.content.tool_use_id == tool_use_response.content.tool_use_id
                ):
                    tool_use_request_message_id = message.id
                    if message.message_type == MessageType.QUERY:
                        main_query_id = message.id
                    elif message.query_id:
                        main_query_id = message.query_id
                    else:
                        raise ValueError("Main query id not found")

                    detected_llm = message.llm_model
                    detected_prompt_handler = self.prompt_handler_map.get_prompt(
                        model_name=detected_llm, feature=self.prompt_features(message.prompt_type)
                    )({})
                    break

        if not tool_use_request_message_id or not detected_llm:
            raise ValueError(
                f"Tool use request message not found for tool use response id {tool_use_response.content.tool_use_id}"
            )

        if not detected_prompt_handler:
            raise ValueError("Prompt handler not found for prompt type")

        conversation_chain_messages = [
            message for message in session_messages if message.id <= tool_use_request_message_id
        ]
        await self.store_tool_use_ressponse_in_db(
            session_id=session_id,
            previous_responses=conversation_chain_messages,
            prompt_type=detected_prompt_handler.prompt_type,
            llm_model=detected_llm,
            tool_use_response=tool_use_response,
            query_id=main_query_id,
            call_chain_category=call_chain_category,
        )

        client = self.model_to_provider_class_map[detected_llm]()

        llm_response = await self.get_llm_response(
            session_id=session_id,
            client=client,
            tool_use_response=tool_use_response,
            tools=tools,
            previous_responses=conversation_chain_messages,
            stream=stream,
            prompt_type=detected_prompt_handler.prompt_type,
            llm_model=detected_llm,
            query_id=main_query_id,
            call_chain_category=call_chain_category,
        )

        return await self.parse_llm_response_data(
            llm_response=llm_response, prompt_handler=detected_prompt_handler, query_id=main_query_id
        )
