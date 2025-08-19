from typing import List

from app.backend_common.services.chat_file_upload.chat_file_upload import ChatFileUpload
from app.backend_common.services.chat_file_upload.dataclasses.chat_file_upload import Attachment
from app.main.blueprints.one_dev.models.dto.agent_chats import (
    AgentChatDTO,
    TextMessageData,
    ToolStatus,
    ToolUseMessageData,
)
from app.main.blueprints.one_dev.services.history.code_gen_agent_chats.dataclasses.code_gen_agent_chats import (
    ChatElement,
)
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
            if isinstance(chat_data.message_data, TextMessageData):
                if chat_data.message_data.directory_items:
                    for item in chat_data.message_data.directory_items:
                        item.structure = None

                if chat_data.message_data.focus_items:
                    for item in chat_data.message_data.focus_items:
                        item.chunks = []

                if chat_data.message_data.attachments:
                    for item in chat_data.message_data.attachments:
                        item.attachment_data = (
                            (await attachment_data_task_map[item.attachment_id])
                            if item.attachment_id in attachment_data_task_map
                            else None
                        )

                if chat_data.message_data.vscode_env:
                    chat_data.message_data.vscode_env = None

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
