import asyncio
import json
import traceback
from enum import Enum
from typing import Any, Dict, Generic, List, Literal, Optional, Sequence, Type, TypeVar, Union

import xxhash
from deputydev_core.utils.app_logger import AppLogger

from app.backend_common.exception import RetryException
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
    FileBlockData,
    FileContent,
    ExtendedThinkingData,
    ExtendedThinkingContent,
)
from app.backend_common.repository.message_threads.repository import (
    MessageThreadsRepository,
)
from app.backend_common.services.chat_file_upload.chat_file_upload import ChatFileUpload
from app.backend_common.services.llm.base_llm_provider import BaseLLMProvider
from app.backend_common.services.llm.dataclasses.main import (
    ChatAttachmentDataWithObjectBytes,
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
from app.backend_common.services.llm.providers.google.llm_provider import Google
from app.backend_common.services.llm.providers.openai.llm_provider import OpenAI
from deputydev_core.utils.config_manager import ConfigManager
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import Attachment
from app.backend_common.repository.chat_attachments.repository import ChatAttachmentsRepository

PromptFeatures = TypeVar("PromptFeatures", bound=Enum)

MAX_LLM_RETRIES = int(ConfigManager.configs["LLM_MAX_RETRY"])


class LLMHandler(Generic[PromptFeatures]):
    model_to_provider_class_map = {
        LLModels.CLAUDE_3_POINT_5_SONNET: Anthropic,
        LLModels.CLAUDE_3_POINT_7_SONNET: Anthropic,
        LLModels.CLAUDE_4_SONNET: Anthropic,
        LLModels.CLAUDE_4_SONNET_THINKING: Anthropic,
        LLModels.GPT_4O: OpenAI,
        LLModels.GPT_40_MINI: OpenAI,
        LLModels.GEMINI_2_POINT_5_PRO: Google,
        LLModels.GEMINI_2_POINT_0_FLASH: Google,
        LLModels.GPT_4_POINT_1: OpenAI,
        LLModels.GPT_O3_MINI: OpenAI,
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
            if event.type == StreamingEventType.EXTENDED_THINKING_BLOCK_START:
                current_content_block = ExtendedThinkingData(
                    type=ContentBlockCategory.EXTENDED_THINKING, content=ExtendedThinkingContent(thinking="")
                )
            elif event.type == StreamingEventType.EXTENDED_THINKING_BLOCK_DELTA:
                if current_content_block and isinstance(current_content_block, ExtendedThinkingData):
                    current_content_block.content.thinking += event.content.thinking_delta
            elif event.type == StreamingEventType.EXTENDED_THINKING_BLOCK_END:
                if current_content_block and isinstance(current_content_block, ExtendedThinkingData):
                    current_content_block.content.signature = event.content.signature
                    non_streaming_content_blocks.append(current_content_block)
                    current_content_block = None
            elif event.type == StreamingEventType.REDACTED_THINKING:
                current_content_block = ExtendedThinkingData(
                    type=ContentBlockCategory.EXTENDED_THINKING,
                    content=ExtendedThinkingContent(type="redacted_thinking", thinking=event.data),
                )
                non_streaming_content_blocks.append(current_content_block)
                current_content_block = None

            elif event.type == StreamingEventType.TEXT_BLOCK_START:
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
        prompt_category: str,
        llm_model: LLModels,
        query_id: int,
        call_chain_category: MessageCallChainCategory,
    ) -> None:
        response_to_use: NonStreamingResponse
        if llm_response.type == LLMCallResponseTypes.STREAMING:
            response_to_use = await self.get_non_streaming_response_from_streaming_response(llm_response)
        else:
            response_to_use = llm_response

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
            prompt_category=prompt_category,
            usage=response_to_use.usage,
            call_chain_category=call_chain_category,
        )
        await MessageThreadsRepository.create_message_thread(message_thread)

    async def store_llm_query_in_db(
        self,
        session_id: int,
        previous_responses: List[MessageThreadDTO],
        prompt_type: str,
        prompt_category: str,
        llm_model: LLModels,
        prompt_rendered_messages: UserAndSystemMessages,
        prompt_vars: Dict[str, Any],
        call_chain_category: MessageCallChainCategory,
        attachmnts: Optional[List[Attachment]],
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
        message_data: List[Union[FileBlockData, TextBlockData]] = [
            TextBlockData(
                type=ContentBlockCategory.TEXT_BLOCK,
                content=TextBlockContent(text=prompt_rendered_messages.user_message),
                content_vars=prompt_vars if prompt_vars else None,
            )
        ]
        if attachmnts:
            for file in attachmnts:
                message_data.append(
                    FileBlockData(
                        type=ContentBlockCategory.FILE,
                        content=FileContent(attachment_id=file.attachment_id),
                    )
                )

        message_thread = MessageThreadData(
            session_id=session_id,
            actor=MessageThreadActor.USER,
            query_id=None,
            message_type=MessageType.QUERY,
            conversation_chain=[message.id for message in previous_responses],
            message_data=message_data,
            data_hash=data_hash,
            prompt_type=prompt_type,
            prompt_category=prompt_category,
            llm_model=llm_model,
            call_chain_category=call_chain_category,
        )
        return await MessageThreadsRepository.create_message_thread(message_thread)

    async def store_user_feedback_in_db(
        self,
        session_id: int,
        previous_responses: List[MessageThreadDTO],
        prompt_type: str,
        prompt_category: str,
        llm_model: LLModels,
        feedback: str,
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
        data_hash = xxhash.xxh64(feedback).hexdigest()
        message_thread = MessageThreadData(
            session_id=session_id,
            actor=MessageThreadActor.USER,
            query_id=None,
            message_type=MessageType.RESPONSE,
            conversation_chain=[message.id for message in previous_responses],
            message_data=[
                TextBlockData(
                    type=ContentBlockCategory.TEXT_BLOCK,
                    content=TextBlockContent(text=feedback),
                )
            ],
            data_hash=data_hash,
            prompt_type=prompt_type,
            prompt_category=prompt_category,
            llm_model=llm_model,
            call_chain_category=call_chain_category,
        )
        return await MessageThreadsRepository.create_message_thread(message_thread)

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

    async def _get_attachment_data_and_metadata(
        self,
        attachment_id: int,
    ) -> ChatAttachmentDataWithObjectBytes:
        """
        Get attachment data and metadata
        """

        attachment_data = await ChatAttachmentsRepository.get_attachment_by_id(attachment_id=attachment_id)
        if not attachment_data:
            raise ValueError(f"Attachment with id {attachment_id} not found")

        s3_key = attachment_data.s3_key
        object_bytes = await ChatFileUpload.get_file_data_by_s3_key(s3_key=s3_key)

        return ChatAttachmentDataWithObjectBytes(attachment_metadata=attachment_data, object_bytes=object_bytes)

    def _get_attachment_data_task_map(
        self,
        previous_responses: List[MessageThreadDTO],
        current_attachments: List[Attachment],
    ) -> Dict[int, asyncio.Task[ChatAttachmentDataWithObjectBytes]]:
        """
        map attachment id to attachment data fetch task
        """

        previous_attachments: List[Attachment] = []
        for message in previous_responses:
            for data in message.message_data:
                if data.type == ContentBlockCategory.FILE:
                    previous_attachments.append(
                        Attachment(
                            attachment_id=data.content.attachment_id,
                        )
                    )

        all_attachments = previous_attachments + current_attachments

        attachment_data_task_map: Dict[int, Any] = {}
        for attachment in all_attachments:
            if attachment.attachment_id not in attachment_data_task_map:
                attachment_data_task_map[attachment.attachment_id] = asyncio.create_task(
                    self._get_attachment_data_and_metadata(attachment_id=attachment.attachment_id)
                )

        return attachment_data_task_map

    async def fetch_and_parse_llm_response(
        self,
        client: BaseLLMProvider,
        session_id: int,
        prompt_type: str,
        llm_model: LLModels,
        query_id: int,
        prompt_handler: BasePrompt,
        call_chain_category: MessageCallChainCategory,
        tools: Optional[List[ConversationTool]] = None,
        tool_choice: Literal["none", "auto", "required"] = "auto",
        user_and_system_messages: Optional[UserAndSystemMessages] = None,
        tool_use_response: Optional[ToolUseResponseData] = None,
        previous_responses: List[MessageThreadDTO] = [],
        feedback: str = None,
        max_retry: int = MAX_LLM_RETRIES,
        stream: bool = False,
        response_type: Optional[str] = None,
        attachments: List[Attachment] = [],
        **kwargs: Any,
    ) -> ParsedLLMCallResponse:
        """
        Fetch LLM response and parse it with retry logic

        Parameters:
            :param client: LLM provider client
            :param session_id: Session id
            :param prompt_type: Type of prompt
            :param llm_model: LLM model to use
            :param query_id: Query id
            :param prompt_handler: Prompt handler
            :param call_chain_category: Call chain category
            :param tools: List of tools
            :param user_and_system_messages: User and system messages
            :param tool_use_response: Tool use response
            :param previous_responses: List of previous responses
            :param max_retry: Maximum number of retries
            :param stream: Stream response
            :param response_type: Response type

        Returns:
            :return: Parsed LLM response
        """
        # check and get attachment data task map
        attachment_data_task_map = self._get_attachment_data_task_map(
            previous_responses=previous_responses,
            current_attachments=attachments,
        )

        if not user_and_system_messages:
            user_and_system_messages = UserAndSystemMessages(system_message=prompt_handler.get_system_prompt())
        for i in range(0, max_retry):
            try:
                llm_payload = await client.build_llm_payload(
                    llm_model,
                    prompt=user_and_system_messages,
                    attachments=attachments,
                    tool_use_response=tool_use_response,
                    previous_responses=previous_responses,
                    tools=tools,
                    tool_choice=tool_choice,
                    cache_config=self.cache_config,
                    feedback=feedback,
                    attachment_data_task_map=attachment_data_task_map,
                    **kwargs,
                )

                llm_response = await client.call_service_client(
                    llm_payload, llm_model, stream=stream, response_type=response_type
                )

                # start task for storing LLM message in DB
                if stream:
                    asyncio.create_task(
                        self.store_llm_response_in_db(
                            llm_response,
                            session_id,
                            prompt_type=prompt_type,
                            prompt_category=prompt_handler.prompt_category,
                            llm_model=llm_model,
                            query_id=query_id,
                            call_chain_category=call_chain_category,
                        )
                    )
                else:
                    await self.store_llm_response_in_db(
                        llm_response,
                        session_id,
                        prompt_type=prompt_type,
                        prompt_category=prompt_handler.prompt_category,
                        llm_model=llm_model,
                        query_id=query_id,
                        call_chain_category=call_chain_category,
                    )

                # Parse the LLM response
                parsed_response = await self.parse_llm_response_data(
                    llm_response=llm_response, prompt_handler=prompt_handler, query_id=query_id
                )
                return parsed_response

            except GeneratorExit:
                # Properly handle GeneratorExit exception when the coroutine is cancelled
                AppLogger.log_warn("LLM response generation was cancelled")
                raise  # Re-raise to properly propagate the exception
            except asyncio.CancelledError:
                AppLogger.log_warn("LLM response task was cancelled")
                raise  # Re-raise to properly propagate the exception
            except json.JSONDecodeError as e:
                AppLogger.log_debug(traceback.format_exc())
                AppLogger.log_warn(f"Retry {i + 1}/{max_retry} JSON decode error: {e}")
                await asyncio.sleep(2)
            except ValueError as e:
                AppLogger.log_debug(traceback.format_exc())
                AppLogger.log_warn(f"Retry {i + 1}/{max_retry} Parse error: {e}")
                await asyncio.sleep(2)
            except Exception as e:
                AppLogger.log_debug(traceback.format_exc())
                AppLogger.log_warn(f"Retry {i + 1}/{max_retry} Error while fetching/parsing data from LLM: {e}")
                await asyncio.sleep(2)

        raise RetryException(f"Failed to get or parse response from LLM after {max_retry} retries")

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
                    actor=(
                        MessageThreadActor.USER if turn.role == ConversationRole.USER else MessageThreadActor.ASSISTANT
                    ),
                    query_id=None,
                    message_type=MessageType.RESPONSE,
                    conversation_chain=[],
                    data_hash=hash,
                    message_data=[],
                    prompt_type=prompt_handler.prompt_type,
                    prompt_category=prompt_handler.prompt_category,
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
        attachments: List[Attachment] = [],
        tools: Optional[List[ConversationTool]] = None,
        tool_choice: Literal["none", "auto", "required"] = "auto",
        previous_responses: Union[List[int], List[ConversationTurn]] = [],
        stream: bool = False,
        call_chain_category: MessageCallChainCategory = MessageCallChainCategory.CLIENT_CHAIN,
        **kwargs,
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
            prompt_category=prompt_handler.prompt_category,
            llm_model=prompt_handler.model_name,
            prompt_rendered_messages=user_and_system_messages,
            prompt_vars=prompt_vars,
            attachmnts=attachments,
            call_chain_category=call_chain_category,
        )
        return await self.fetch_and_parse_llm_response(
            client=client,
            session_id=session_id,
            prompt_type=prompt_handler.prompt_type,
            llm_model=prompt_handler.model_name,
            query_id=prompt_thread.id,
            prompt_handler=prompt_handler,
            call_chain_category=call_chain_category,
            tools=tools,
            tool_choice=tool_choice,
            user_and_system_messages=user_and_system_messages,
            attachments=attachments,
            previous_responses=conversation_chain_messages,
            max_retry=MAX_LLM_RETRIES,
            stream=stream,
            response_type=prompt_handler.response_type,
            **kwargs,
        )

    async def store_tool_use_ressponse_in_db(
        self,
        session_id: int,
        tool_use_response: ToolUseResponseData,
        prompt_type: str,
        prompt_category: str,
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
            prompt_category=prompt_category,
            llm_model=llm_model,
            call_chain_category=call_chain_category,
        )
        return await MessageThreadsRepository.create_message_thread(message_thread)

    async def submit_tool_use_response(
        self,
        session_id: int,
        tool_use_response: ToolUseResponseData,
        tools: Optional[List[ConversationTool]] = None,
        tool_choice: Literal["none", "auto", "required"] = "auto",
        stream: bool = False,
        call_chain_category: MessageCallChainCategory = MessageCallChainCategory.CLIENT_CHAIN,
        prompt_type=None,
        prompt_vars: dict = None,
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
        if not prompt_vars:
            prompt_vars = {}
        session_messages = await MessageThreadsRepository.get_message_threads_for_session(
            session_id=session_id, call_chain_category=call_chain_category, prompt_type=prompt_type
        )
        session_messages.sort(key=lambda x: x.id)
        filtered_messages = [message for message in session_messages if message.message_type == MessageType.RESPONSE]

        detected_llm: Optional[LLModels] = None
        tool_use_request_message_id = None
        detected_prompt_handler: Optional[BasePrompt] = None
        selected_prev_query_ids = []
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
                        selected_prev_query_ids = message.conversation_chain
                    elif message.query_id:
                        main_query_id = message.query_id
                    else:
                        raise ValueError("Main query id not found")

                    detected_llm = message.llm_model
                    detected_prompt_handler = self.prompt_handler_map.get_prompt(
                        model_name=detected_llm, feature=self.prompt_features(message.prompt_type)
                    )(prompt_vars)
                    break

        if not tool_use_request_message_id or not detected_llm:
            raise ValueError(
                f"Tool use request message not found for tool use response id {tool_use_response.content.tool_use_id}"
            )

        if not detected_prompt_handler:
            raise ValueError("Prompt handler not found for prompt type")

        conversation_chain_messages = [
            message
            for message in session_messages
            if message.id <= tool_use_request_message_id
            and (
                (message.id in selected_prev_query_ids or message.query_id in selected_prev_query_ids)
                or not selected_prev_query_ids
            )
        ]

        await self.store_tool_use_ressponse_in_db(
            session_id=session_id,
            previous_responses=conversation_chain_messages,
            prompt_type=detected_prompt_handler.prompt_type,
            prompt_category=detected_prompt_handler.prompt_category,
            llm_model=detected_llm,
            tool_use_response=tool_use_response,
            query_id=main_query_id,
            call_chain_category=call_chain_category,
        )

        client = self.model_to_provider_class_map[detected_llm]()

        return await self.fetch_and_parse_llm_response(
            client=client,
            session_id=session_id,
            prompt_type=detected_prompt_handler.prompt_type,
            llm_model=detected_llm,
            query_id=main_query_id,
            prompt_handler=detected_prompt_handler,
            call_chain_category=call_chain_category,
            tools=tools,
            tool_choice=tool_choice,
            tool_use_response=tool_use_response,
            previous_responses=conversation_chain_messages,
            max_retry=MAX_LLM_RETRIES,
            stream=stream,
        )

    async def submit_feedback_response(
        self,
        session_id: int,
        feedback: str,
        tools: Optional[List[ConversationTool]] = None,
        stream: bool = False,
        call_chain_category: MessageCallChainCategory = MessageCallChainCategory.CLIENT_CHAIN,
        prompt_type=None,
    ) -> ParsedLLMCallResponse:
        session_messages = await MessageThreadsRepository.get_message_threads_for_session(
            session_id=session_id, call_chain_category=call_chain_category, prompt_type=prompt_type
        )
        session_messages.sort(key=lambda x: x.id)

        detected_llm = session_messages[0].llm_model
        detected_prompt_handler = self.prompt_handler_map.get_prompt(
            model_name=detected_llm, feature=self.prompt_features(prompt_type)
        )({})

        if not detected_prompt_handler:
            raise ValueError("Prompt handler not found for prompt type")

        conversation_chain_messages = session_messages
        # Feedback for last message of that session
        main_query_id = session_messages[-1].id

        await self.store_user_feedback_in_db(
            session_id=session_id,
            previous_responses=conversation_chain_messages,
            prompt_type=prompt_type,
            prompt_category=detected_prompt_handler.prompt_category,
            llm_model=detected_prompt_handler.model_name,
            feedback=feedback,
            call_chain_category=call_chain_category,
        )

        client = self.model_to_provider_class_map[detected_llm]()

        return await self.fetch_and_parse_llm_response(
            client=client,
            session_id=session_id,
            prompt_type=detected_prompt_handler.prompt_type,
            llm_model=detected_llm,
            query_id=main_query_id,
            prompt_handler=detected_prompt_handler,
            call_chain_category=call_chain_category,
            feedback=feedback,
            tools=tools,
            previous_responses=conversation_chain_messages,
            max_retry=MAX_LLM_RETRIES,
            stream=stream,
        )
