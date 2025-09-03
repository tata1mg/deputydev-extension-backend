import asyncio
from datetime import datetime
from typing import Any, Dict, List, Tuple

from deputydev_core.services.chunking.chunk_info import ChunkInfo
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
from app.backend_common.utils.sanic_wrapper import CONFIG
from app.backend_common.utils.tortoise_wrapper import TortoiseWrapper
from app.main.blueprints.one_dev.constants.tools import ToolStatus
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
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    ClassFocusItem,
    CodeSnippetFocusItem,
    FileFocusItem,
    FocusItem,
    FunctionFocusItem,
    Repository,
    UrlFocusItem,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.factory import (
    PromptFeatureFactory,
)
from app.main.blueprints.one_dev.services.repository.agent_chats.repository import AgentChatsRepository


class MessageThreadMigrationManager:
    @classmethod
    async def migrate_batch_of_sessions(cls) -> int:  # noqa: C901
        """
        Migrate message threads to agent chats.
        This method simulates the migration process.
        """
        batch_size = 100
        unmigrated_sessions = await ExtensionSessionsRepository.get_unmigrated_sessions(limit=batch_size)
        print(f"Unmigrated sessions found: {len(unmigrated_sessions)}")  # noqa: T201
        total_migrated_sessions = 0

        for session in unmigrated_sessions:
            message_threads = await MessageThreadsRepository.get_message_threads_for_session(
                session_id=session.session_id,
                call_chain_category=MessageCallChainCategory.CLIENT_CHAIN,
                prompt_types=["CODE_QUERY_SOLVER", "CUSTOM_CODE_QUERY_SOLVER"],
            )
            message_threads.sort(key=lambda x: x.created_at)
            corresponding_agent_chats_and_dates: List[Tuple[AgentChatData, datetime, datetime, int]] = []
            last_llm_model = None
            migrated_message_thread_ids: List[int] = []
            for message_thread in message_threads:
                if message_thread.llm_model != last_llm_model:
                    last_llm_model = message_thread.llm_model
                try:
                    if (
                        message_thread.actor == MessageThreadActor.USER
                        and message_thread.message_type == MessageType.QUERY
                    ):
                        query_vars: Dict[str, Any] | None = None
                        file_blocks: List[FileBlockData] = []
                        for query_message_content in message_thread.message_data:
                            if isinstance(query_message_content, TextBlockData):
                                query_vars = query_message_content.content_vars
                            elif isinstance(query_message_content, FileBlockData):
                                file_blocks.append(query_message_content)
                        if not query_vars:
                            AppLogger.log_error(f"Query variables not found for message_thread: {message_thread.id}")
                            continue

                        focus_items: List[FocusItem] = []

                        try:
                            if query_vars.get("focus_items"):
                                for focus_item in query_vars["focus_items"]:
                                    if focus_item.get("type") == "file":
                                        focus_items.append(
                                            FileFocusItem(
                                                value=focus_item["value"],
                                                chunks=[
                                                    ChunkInfo(**focus_chunk) for focus_chunk in focus_item["chunks"]
                                                ],
                                                path=focus_item["path"],
                                            )
                                        )

                                    if focus_item.get("type") == "code_snippet":
                                        focus_items.append(
                                            CodeSnippetFocusItem(
                                                value=focus_item["value"],
                                                chunks=[
                                                    ChunkInfo(**focus_chunk) for focus_chunk in focus_item["chunks"]
                                                ],
                                                path=focus_item["path"],
                                            )
                                        )

                                    if focus_item.get("type") == "function":
                                        focus_items.append(
                                            FunctionFocusItem(
                                                value=focus_item["value"],
                                                chunks=[
                                                    ChunkInfo(**focus_chunk) for focus_chunk in focus_item["chunks"]
                                                ],
                                                path=focus_item["path"],
                                            )
                                        )

                                    if focus_item.get("type") == "class":
                                        focus_items.append(
                                            ClassFocusItem(
                                                value=focus_item["value"],
                                                chunks=[
                                                    ChunkInfo(**focus_chunk) for focus_chunk in focus_item["chunks"]
                                                ],
                                                path=focus_item["path"],
                                            )
                                        )

                            if query_vars.get("urls"):
                                for url in query_vars["urls"]:
                                    focus_items.append(
                                        UrlFocusItem(
                                            value=url["value"],
                                            url=url["url"],
                                        )
                                    )

                        except Exception as ex:  # noqa: BLE001
                            AppLogger.log_error(
                                f"Error occurred while processing focus items: {ex} for {message_thread.id}"
                            )

                        corresponding_agent_chats_and_dates.append(
                            (
                                AgentChatData(
                                    actor=ActorType.USER,
                                    message_type=AgentMessageType.TEXT,
                                    message_data=TextMessageData(
                                        text=query_vars["query"],
                                        attachments=[
                                            Attachment(attachment_id=block.content.attachment_id)
                                            for block in file_blocks
                                        ],
                                        vscode_env=query_vars.get("vscode_env") or None,
                                        focus_items=focus_items,
                                        repositories=[
                                            Repository(**_rep_data)
                                            for _rep_data in query_vars.get("repositories") or []
                                        ],
                                    ),
                                    metadata=message_thread.metadata or {},
                                    session_id=session.session_id,
                                    query_id=f"{message_thread.id}",
                                    previous_queries=[],
                                ),
                                message_thread.created_at,
                                message_thread.updated_at,
                                message_thread.id,  # Store the message_thread id for later use
                            )
                        )

                    if (
                        message_thread.actor == MessageThreadActor.USER
                        and message_thread.message_type == MessageType.TOOL_RESPONSE
                    ):
                        tool_response_message_content = message_thread.message_data[0]
                        if not isinstance(tool_response_message_content, ToolUseResponseData):
                            AppLogger.log_error(
                                f"Tool response message content is not of type ToolUseResponseData for message_thread: {message_thread.id}"
                            )
                            continue
                        corresponding_tool_request = next(
                            (
                                req
                                for req, _created_at, _updated_at, _message_thread_id in corresponding_agent_chats_and_dates
                                if isinstance(req.message_data, ToolUseMessageData)
                                and req.message_data.tool_use_id == tool_response_message_content.content.tool_use_id
                            ),
                            None,
                        )
                        if not corresponding_tool_request or not isinstance(
                            corresponding_tool_request.message_data, ToolUseMessageData
                        ):
                            AppLogger.log_error(
                                f"Corresponding tool request not found or invalid for message_thread: {message_thread.id}"
                            )
                            continue

                        # update tool response
                        corresponding_tool_request.message_data.tool_response = (
                            tool_response_message_content.content.response
                            if isinstance(tool_response_message_content.content.response, dict)
                            else {"response": tool_response_message_content.content.response}
                        )
                        corresponding_tool_request.message_data.tool_status = ToolStatus.COMPLETED

                    if (
                        message_thread.actor == MessageThreadActor.ASSISTANT
                        and message_thread.message_type == MessageType.RESPONSE
                    ):
                        for assistant_response_block in message_thread.message_data:
                            if isinstance(assistant_response_block, TextBlockData):
                                prompt_feature = PromptFeatures(message_thread.prompt_type)
                                parser_class = PromptFeatureFactory.get_prompt(message_thread.llm_model, prompt_feature)
                                parsed_blocks, _tool_use_map = parser_class.get_parsed_response_blocks(
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
                                        corresponding_agent_chats_and_dates.append(
                                            (
                                                AgentChatData(
                                                    actor=ActorType.ASSISTANT,
                                                    message_type=AgentMessageType.THINKING,
                                                    message_data=ThinkingInfoData(thinking_summary=thinking_text),
                                                    metadata=message_thread.metadata or {},
                                                    session_id=session.session_id,
                                                    query_id=f"{message_thread.query_id}",
                                                    previous_queries=[],
                                                ),
                                                message_thread.created_at,
                                                message_thread.updated_at,
                                                message_thread.id,  # Store the message_thread id for later use
                                            )
                                        )

                                    elif parsed_block["type"] == "TEXT_BLOCK":
                                        text_content = parsed_block["content"]["text"]
                                        corresponding_agent_chats_and_dates.append(
                                            (
                                                AgentChatData(
                                                    actor=ActorType.ASSISTANT,
                                                    message_type=AgentMessageType.TEXT,
                                                    message_data=TextMessageData(text=text_content),
                                                    metadata=message_thread.metadata or {},
                                                    session_id=session.session_id,
                                                    query_id=f"{message_thread.query_id}",
                                                    previous_queries=[],
                                                ),
                                                message_thread.created_at,
                                                message_thread.updated_at,
                                                message_thread.id,  # Store the message_thread id for later use
                                            )
                                        )

                                    elif parsed_block["type"] == "CODE_BLOCK":
                                        language = parsed_block["content"]["language"]
                                        file_path = parsed_block["content"]["file_path"]
                                        code = parsed_block["content"]["code"]
                                        diff = parsed_block["content"].get("diff")
                                        corresponding_agent_chats_and_dates.append(
                                            (
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
                                                    session_id=session.session_id,
                                                    query_id=f"{message_thread.query_id}",
                                                    previous_queries=[],
                                                ),
                                                message_thread.created_at,
                                                message_thread.updated_at,
                                                message_thread.id,  # Store the message_thread id for later use
                                            )
                                        )

                            elif isinstance(assistant_response_block, ToolUseRequestData):
                                corresponding_agent_chats_and_dates.append(
                                    (
                                        AgentChatData(
                                            actor=ActorType.ASSISTANT,
                                            message_type=AgentMessageType.TOOL_USE,
                                            message_data=ToolUseMessageData(
                                                tool_use_id=assistant_response_block.content.tool_use_id,
                                                tool_name=assistant_response_block.content.tool_name,
                                                tool_input=assistant_response_block.content.tool_input,
                                            ),
                                            metadata=message_thread.metadata or {},
                                            session_id=session.session_id,
                                            query_id=f"{message_thread.query_id}",
                                            previous_queries=[],
                                        ),
                                        message_thread.created_at,
                                        message_thread.updated_at,
                                        message_thread.id,  # Store the message_thread id for later use
                                    )
                                )

                            elif isinstance(assistant_response_block, ExtendedThinkingData):
                                corresponding_agent_chats_and_dates.append(
                                    (
                                        AgentChatData(
                                            actor=ActorType.ASSISTANT,
                                            message_type=AgentMessageType.THINKING,
                                            message_data=ThinkingInfoData(
                                                thinking_summary=assistant_response_block.content.thinking
                                            ),
                                            metadata=message_thread.metadata or {},
                                            session_id=session.session_id,
                                            query_id=f"{message_thread.query_id}",
                                            previous_queries=[],
                                        ),
                                        message_thread.created_at,
                                        message_thread.updated_at,
                                        message_thread.id,  # Store the message_thread id for later use
                                    )
                                )
                    print(f"Corresponding agent chats created for message_thread {message_thread.id}")  # noqa: T201
                    migrated_message_thread_ids.append(message_thread.id)
                except Exception as ex:  # noqa: BLE001
                    AppLogger.log_error(
                        f"Error occurred while migrating message_thread, ex: {ex}, message_thread_id: {message_thread.id}"
                    )

            try:
                saved = False
                unsaved_msg_thread_ids: List[int] = []
                if corresponding_agent_chats_and_dates and migrated_message_thread_ids and last_llm_model:
                    # now insert all the corresponding agent chats in the table
                    for (
                        agent_chat,
                        created_datetime,
                        updated_datetime,
                        msg_thr_id,
                    ) in corresponding_agent_chats_and_dates:
                        try:
                            await AgentChatsRepository.create_chat(
                                chat_data=AgentChatCreateRequest(
                                    session_id=agent_chat.session_id,
                                    query_id=agent_chat.query_id,
                                    actor=agent_chat.actor,
                                    message_type=agent_chat.message_type,
                                    message_data=agent_chat.message_data,
                                    metadata=agent_chat.metadata or {},
                                    previous_queries=agent_chat.previous_queries,
                                ),
                                custom_created_at=created_datetime,
                                custom_updated_at=updated_datetime,
                            )
                            saved = True
                        except Exception as ex:  # noqa: BLE001
                            AppLogger.log_error(
                                f"Error occurred while saving agent chat for session {session.session_id}, ex: {ex} - message_thread_id: {msg_thr_id}"
                            )
                            unsaved_msg_thread_ids.append(msg_thr_id)

                    print(f"Corresponding agent chats saved for session {session.session_id}")  # noqa: T201

                    # mark the last used LLM in the session
                    if saved:
                        await ExtensionSessionsRepository.update_session_llm_model(
                            session_id=session.session_id, llm_model=last_llm_model
                        )

                        # mark all message_threads as migrated
                        final_migrated_message_thread_ids = [
                            _msg_thr_id
                            for _msg_thr_id in migrated_message_thread_ids
                            if _msg_thr_id not in unsaved_msg_thread_ids
                        ]
                        await MessageThreadsRepository.mark_as_migrated(final_migrated_message_thread_ids)
                        print(f"Message threads marked as migrated for session {session.session_id}")  # noqa: T201
                        total_migrated_sessions += 1

                    else:
                        AppLogger.log_error(f"Agent chats not saved for session {session.session_id}")
                        raise ValueError(f"Agent chats not saved for session {session.session_id}")

                    await asyncio.sleep(0.1)  # to avoid hitting the database too hard

                else:
                    raise ValueError(
                        f"No corresponding agent chats found for session {session.session_id} or no message threads to migrate. Values for len(corresponding_agent_chats_and_dates): {len(corresponding_agent_chats_and_dates)}, len(migrated_message_thread_ids): {len(migrated_message_thread_ids)}, last_llm_model: {last_llm_model}"
                    )

            except Exception as ex:  # noqa: BLE001
                AppLogger.log_error(f"Error occurred while migrating session, ex: {ex}")

        return total_migrated_sessions

    @classmethod
    async def migrate_to_agent_chats(cls) -> None:
        await TortoiseWrapper.setup(config={}, orm_config=CONFIG.config["DB_CONNECTIONS"])
        # migrate all
        while True:
            migrated_count = await cls.migrate_batch_of_sessions()
            if migrated_count == 0:
                break

        print("Migration to agent chats completed.")  # noqa: T201
