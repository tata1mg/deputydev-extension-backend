from typing import List

from app.backend_common.repository.chat_attachments.repository import ChatAttachmentsRepository
from app.backend_common.services.chat_file_upload.chat_file_upload import ChatFileUpload
from app.backend_common.services.chat_file_upload.dataclasses.chat_file_upload import Attachment
from app.main.blueprints.one_dev.models.dto.agent_chats import (
    ActorType,
    AgentChatDTO,
    TextMessageData,
    ToolStatus,
    ToolUseMessageData,
)
from app.main.blueprints.one_dev.services.history.code_gen_agent_chats.dataclasses.code_gen_agent_chats import (
    ChatElement,
)
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    ClassFocusItem,
    CodeSnippetFocusItem,
    DirectoryFocusItem,
    FileFocusItem,
    FunctionFocusItem,
)
from app.main.blueprints.one_dev.services.query_solver.tools.ask_user_input import ASK_USER_INPUT
from app.main.blueprints.one_dev.services.repository.agent_chats.repository import AgentChatsRepository


class PastCodeGenAgentChatsManager:
    """
    A class to handle operations related to past workflows, including fetching past sessions and chats.
    """

    @classmethod
    async def get_serialized_previous_chat_data(cls, raw_agent_chats: List[AgentChatDTO]) -> List[ChatElement]:  # noqa: C901
        all_attachments: List[Attachment] = []
        for chat_data in raw_agent_chats:
            if isinstance(chat_data.message_data, TextMessageData):
                all_attachments.extend(chat_data.message_data.attachments)

        attachment_data_task_map = ChatFileUpload.get_attachment_data_task_map(all_attachments=all_attachments)
        all_elements: List[ChatElement] = []

        for chat_data in raw_agent_chats:
            # special handling for ask user input
            if (
                isinstance(chat_data.message_data, ToolUseMessageData)
                and chat_data.message_data.tool_name == ASK_USER_INPUT.name
            ):
                all_elements.append(
                    ChatElement(
                        actor=ActorType.ASSISTANT,
                        message_data=TextMessageData(text=chat_data.message_data.tool_input["prompt"]),
                        timestamp=chat_data.created_at,
                    )
                )
                if chat_data.message_data.tool_response and "user_response" in chat_data.message_data.tool_response:
                    all_elements.append(
                        ChatElement(
                            actor=ActorType.USER,
                            message_data=TextMessageData(text=chat_data.message_data.tool_response["user_response"]),
                            timestamp=chat_data.created_at,
                        )
                    )
                continue

            # formatting
            if isinstance(chat_data.message_data, TextMessageData):
                for focus_item in chat_data.message_data.focus_items:
                    if isinstance(focus_item, DirectoryFocusItem):
                        focus_item.structure = None

                    if (
                        isinstance(focus_item, FileFocusItem)
                        or isinstance(focus_item, ClassFocusItem)
                        or isinstance(focus_item, FunctionFocusItem)
                        or isinstance(focus_item, CodeSnippetFocusItem)
                    ):
                        focus_item.chunks = []

                filtered_attachments: List[Attachment] = []
                if chat_data.message_data.attachments:
                    for item in chat_data.message_data.attachments:
                        attachment_data_from_db = await ChatAttachmentsRepository.get_attachment_by_id(
                            item.attachment_id
                        )
                        if not attachment_data_from_db or attachment_data_from_db.status == "deleted":
                            continue
                        item.attachment_data = (
                            (await attachment_data_task_map[item.attachment_id])
                            if item.attachment_id in attachment_data_task_map
                            else None
                        )
                        if item.attachment_data:
                            item.attachment_data.object_bytes = None
                            presigned_url = await ChatFileUpload.get_presigned_url_for_fetch_by_s3_key(
                                attachment_data_from_db.s3_key
                            )
                            item.get_url = presigned_url
                            filtered_attachments.append(item)

                chat_data.message_data.attachments = filtered_attachments

                if chat_data.message_data.vscode_env:
                    chat_data.message_data.vscode_env = None

                if chat_data.message_data.repositories:
                    chat_data.message_data.repositories = None

            if isinstance(chat_data.message_data, ToolUseMessageData):
                chat_data.message_data.tool_status = (
                    ToolStatus.ABORTED
                    if chat_data.message_data.tool_status == ToolStatus.PENDING
                    else chat_data.message_data.tool_status
                )

            element = ChatElement(
                actor=chat_data.actor,
                message_data=chat_data.message_data,
                timestamp=chat_data.created_at,
            )
            all_elements.append(element)
        return all_elements

    @classmethod
    async def get_past_chats(cls, session_id: int) -> List[ChatElement]:
        """
        Fetch past chats.

        Returns:
            List[ChatElement]: A list of processed past chat data.

        Raises:
            ValueError: If there is an issue with the data retrieval.
            NotImplementedError: If the serializer method is not implemented.
            Exception: For any other errors encountered during the process.
        """
        raw_agent_chats = await AgentChatsRepository.get_chats_by_session_id(session_id=session_id)
        processed_data = await cls.get_serialized_previous_chat_data(raw_agent_chats=raw_agent_chats)
        return processed_data
