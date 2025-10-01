from typing import Any, Dict, List, Optional

from deputydev_core.services.chunking.chunk_info import ChunkInfo

from app.backend_common.utils.tool_response_parser import LLMResponseFormatter
from app.main.blueprints.one_dev.constants.tools import ToolStatus
from app.main.blueprints.one_dev.models.dto.agent_chats import (
    AgentChatDTO,
    AgentChatUpdateRequest,
    ToolUseMessageData,
)
from app.main.blueprints.one_dev.models.dto.agent_chats import MessageType as ChatMessageType
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    FocusItem,
    ToolUseResponseInput,
)
from app.main.blueprints.one_dev.services.repository.agent_chats.repository import AgentChatsRepository


class ToolResponseManager:
    """Handle tool response operations for QuerySolver."""

    def format_tool_response(
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

    async def store_tool_response_in_chat_chain(
        self,
        tool_response: ToolUseResponseInput,
        session_id: int,
        vscode_env: Optional[str],
        focus_items: Optional[List[FocusItem]],
    ) -> AgentChatDTO:
        """Store tool response in the chat chain."""
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

        formatted_response_data = self.format_tool_response(tool_response, vscode_env, focus_items)
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