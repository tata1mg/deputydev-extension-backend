from typing import List

from deputydev_core.utils.app_logger import AppLogger

from app.backend_common.models.dto.message_thread_dto import (
    ExtendedThinkingData,
    FileBlockData,
    MessageCallChainCategory,
    MessageThreadActor,
    MessageType,
    TextBlockData,
    ToolUseRequestData,
    ToolUseResponseData,
)
from app.backend_common.repository.extension_sessions.repository import ExtensionSessionsRepository
from app.backend_common.repository.message_threads.repository import MessageThreadsRepository
from app.backend_common.services.chat_file_upload.dataclasses.chat_file_upload import Attachment
from app.main.blueprints.one_dev.models.dto.agent_chats import (
    ActorType,
    AgentChatCreateRequest,
    AgentChatData,
    CodeBlockData,
    TextMessageData,
    ThinkingInfoData,
    ToolUseMessageData,
)
from app.main.blueprints.one_dev.models.dto.agent_chats import MessageType as AgentMessageType
from app.main.blueprints.one_dev.services.query_solver.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.factory import (
    PromptFeatureFactory,
)
from app.main.blueprints.one_dev.services.repository.agent_chats.repository import AgentChatsRepository


class MessageThreadMigrationManager:
    @classmethod
    async def migrate_to_agent_chats(cls) -> None:  # noqa: C901
        """
        Migrate message threads to agent chats.
        This method simulates the migration process.
        """
        batch_size = 100
        unmigrated_sessions = await ExtensionSessionsRepository.get_unmigrated_sessions(limit=batch_size)

        for session in unmigrated_sessions:
            message_threads = await MessageThreadsRepository.get_message_threads_for_session(
                session_id=session.id,
                call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
                prompt_types=["CODE_QUERY_SOLVER", "CUSTOM_CODE_QUERY_SOLVER"],
            )
            message_threads.sort(key=lambda x: x.created_at)
            corresponding_agent_chats: List[AgentChatData] = []
            last_llm_model = None
            for message_thread in message_threads:
                if message_thread.llm_model != last_llm_model:
                    last_llm_model = message_thread.llm_model
                try:
                    if (
                        message_thread.actor == MessageThreadActor.USER
                        and message_thread.message_type == MessageType.QUERY
                    ):
                        text_block_data: TextBlockData | None = None
                        file_blocks: List[FileBlockData] = []
                        for query_message_content in message_thread.message_data:
                            if isinstance(query_message_content, TextBlockData):
                                text_block_data = query_message_content
                            elif isinstance(query_message_content, FileBlockData):
                                file_blocks.append(query_message_content)
                        if not text_block_data:
                            continue

                        corresponding_agent_chats.append(
                            AgentChatData(
                                actor=ActorType.USER,
                                message_type=AgentMessageType.TEXT,
                                message_data=TextMessageData(
                                    text=text_block_data.content.text,
                                    attachments=[
                                        Attachment(attachment_id=block.content.attachment_id) for block in file_blocks
                                    ],
                                ),
                                metadata=message_thread.metadata or {},
                                session_id=session.id,
                                query_id=f"{message_thread.query_id}",
                                previous_queries=[],
                            )
                        )

                    if (
                        message_thread.actor == MessageThreadActor.USER
                        and message_thread.message_type == MessageType.TOOL_RESPONSE
                    ):
                        tool_response_message_content = message_thread.message_data[0]
                        if not isinstance(tool_response_message_content, ToolUseResponseData):
                            continue
                        corresponding_tool_request = next(
                            (
                                req
                                for req in corresponding_agent_chats
                                if isinstance(req.message_data, ToolUseMessageData)
                                and req.message_data.tool_use_id == tool_response_message_content.content.tool_use_id
                            ),
                            None,
                        )
                        if not corresponding_tool_request or not isinstance(
                            corresponding_tool_request.message_data, ToolUseMessageData
                        ):
                            continue

                        # update tool response
                        corresponding_tool_request.message_data.tool_response = (
                            tool_response_message_content.content.response
                            if isinstance(tool_response_message_content.content.response, dict)
                            else {"response": tool_response_message_content.content.response}
                        )

                    if (
                        message_thread.actor == MessageThreadActor.ASSISTANT
                        and message_thread.message_type == MessageType.RESPONSE
                    ):
                        for assistant_response_block in message_thread.message_data:
                            if isinstance(assistant_response_block, TextBlockData):
                                prompt_feature = PromptFeatures(message_thread.prompt_type)
                                parser_class = PromptFeatureFactory.get_prompt(message_thread.llm_model, prompt_feature)
                                parsed_blocks, _tool_use_map = await parser_class.get_parsed_response_blocks(
                                    [assistant_response_block]
                                )
                                if not isinstance(parsed_blocks, list):
                                    AppLogger.log_error(
                                        f"Parsed blocks are not a list for message_thread: {message_thread.id}"
                                    )
                                    continue
                                for parsed_block in parsed_blocks:
                                    if parsed_block["type"] == "THINKING_BLOCK":
                                        thinking_text = parsed_block["content"]["text"]
                                        corresponding_agent_chats.append(
                                            AgentChatData(
                                                actor=ActorType.ASSISTANT,
                                                message_type=AgentMessageType.THINKING,
                                                message_data=ThinkingInfoData(thinking_summary=thinking_text),
                                                metadata=message_thread.metadata or {},
                                                session_id=session.id,
                                                query_id=f"{message_thread.query_id}",
                                                previous_queries=[],
                                            )
                                        )

                                    elif parsed_block["type"] == "TEXT_BLOCK":
                                        text_content = parsed_block["content"]["text"]
                                        corresponding_agent_chats.append(
                                            AgentChatData(
                                                actor=ActorType.ASSISTANT,
                                                message_type=AgentMessageType.TEXT,
                                                message_data=TextMessageData(text=text_content),
                                                metadata=message_thread.metadata or {},
                                                session_id=session.id,
                                                query_id=f"{message_thread.query_id}",
                                                previous_queries=[],
                                            )
                                        )

                                    elif parsed_block["type"] == "CODE_BLOCK":
                                        language = parsed_block["content"]["language"]
                                        file_path = parsed_block["content"]["file_path"]
                                        code = parsed_block["content"]["code"]
                                        diff = parsed_block["content"].get("diff")
                                        corresponding_agent_chats.append(
                                            AgentChatData(
                                                actor=ActorType.ASSISTANT,
                                                message_type=AgentMessageType.CODE_BLOCK,
                                                message_data=CodeBlockData(
                                                    code=code,
                                                    language=language,
                                                    file_path=file_path,
                                                    diff=diff if diff else None,
                                                ),
                                                metadata=message_thread.metadata or {},
                                                session_id=session.id,
                                                query_id=f"{message_thread.query_id}",
                                                previous_queries=[],
                                            )
                                        )

                            elif isinstance(assistant_response_block, ToolUseRequestData):
                                corresponding_agent_chats.append(
                                    AgentChatData(
                                        actor=ActorType.ASSISTANT,
                                        message_type=AgentMessageType.TOOL_USE,
                                        message_data=ToolUseMessageData(
                                            tool_use_id=assistant_response_block.content.tool_use_id,
                                            tool_name=assistant_response_block.content.tool_name,
                                            tool_input=assistant_response_block.content.tool_input,
                                        ),
                                        metadata=message_thread.metadata or {},
                                        session_id=session.id,
                                        query_id=f"{message_thread.query_id}",
                                        previous_queries=[],
                                    )
                                )

                            elif isinstance(assistant_response_block, ExtendedThinkingData):
                                corresponding_agent_chats.append(
                                    AgentChatData(
                                        actor=ActorType.ASSISTANT,
                                        message_type=AgentMessageType.THINKING,
                                        message_data=ThinkingInfoData(
                                            thinking_summary=assistant_response_block.content.thinking
                                        ),
                                        metadata=message_thread.metadata or {},
                                        session_id=session.id,
                                        query_id=f"{message_thread.query_id}",
                                        previous_queries=[],
                                    )
                                )

                except Exception as ex:  # noqa: BLE001
                    AppLogger.log_error(f"Error occurred while migrating message_thread, ex: {ex}")

            try:
                # now insert all the corresponding agent chats in the table
                for agent_chat in corresponding_agent_chats:
                    await AgentChatsRepository.create_chat(
                        chat_data=AgentChatCreateRequest(
                            session_id=agent_chat.session_id,
                            query_id=agent_chat.query_id,
                            actor=agent_chat.actor,
                            message_type=agent_chat.message_type,
                            message_data=agent_chat.message_data,
                            metadata=agent_chat.metadata or {},
                            previous_queries=agent_chat.previous_queries,
                        )
                    )

                # mark the last used LLM in the session
                if last_llm_model:
                    await ExtensionSessionsRepository.update_session_llm_model(
                        session_id=session.id, llm_model=last_llm_model
                    )

                # mark all message_threads as migrated
                await MessageThreadsRepository.mark_as_migrated(session.id)

            except Exception as ex:  # noqa: BLE001
                AppLogger.log_error(f"Error occurred while migrating session, ex: {ex}")
