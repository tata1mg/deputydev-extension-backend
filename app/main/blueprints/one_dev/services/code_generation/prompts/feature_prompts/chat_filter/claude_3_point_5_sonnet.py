import re
from typing import Any, AsyncIterator, Dict, List

from pydantic import BaseModel

from app.backend_common.dataclasses.dataclasses import PromptCategories
from app.backend_common.models.dto.message_thread_dto import ContentBlockCategory
from app.backend_common.services.llm.dataclasses.main import (
    NonStreamingResponse,
    StreamingResponse,
    UserAndSystemMessages,
)
from app.backend_common.services.llm.providers.anthropic.prompts.base_prompts.base_claude_3_point_5_sonnet_prompt_handler import (
    BaseClaude3Point5SonnetPromptHandler,
)
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.previous_chats.dataclasses.main import (
    PreviousChats,
)


class Claude3Point5RelevantChatFilterPrompt(BaseClaude3Point5SonnetPromptHandler):
    prompt_type = "CHAT_RE_RANKING"
    prompt_category = PromptCategories.CODE_GENERATION.value

    def __init__(self, params: Dict[str, Any]):
        self.params = params

    def _create_xml_chats(self, previous_chats: List[PreviousChats]) -> str:
        """
        Create an XML representation of a list of PreviousChats objects.

        Args:
            previous_chats (List[PreviousChats]): List of PreviousChats objects.

        Returns:
            str: XML string.
        """
        # Root element
        xml_output = "<PreviousChatsList>"

        # Add each chat to the XML structure
        for chat in previous_chats:
            xml_output += "<Chat>"
            xml_output += f"<ID>{chat.id}</ID>"
            xml_output += f"<Summary>{chat.summary}</Summary>"
            if chat.query:
                xml_output += f"<Query>{chat.query}</Query>"
            xml_output += "</Chat>"

        # Close root element
        xml_output += "</PreviousChatsList>"

        return xml_output

    def get_prompt(self) -> UserAndSystemMessages:
        user_message = f"""
            Please sort and filter the following chat history based on the user's query, so that it can be used as a context for a LLM to answer the query.
            <chat_history>
            {self._create_xml_chats(self.params["chats"])}
            </chat_history>
            The user query is as follows -
            <user_query>{self.params.get("query")}</user_query>

            <important>
            Please do check and ensure that you keep most of the chunks that are relevant. If one function is selected, keep all chunks related to that function.
            Keep all the chats that are relevant to the user query, do not be too forceful in removing out context. Keep max 5 most relevant chats.
            </important>

            Please return the sorted and filtered chats in the following format:
            <sorted_and_filtered_chat>
            <chat>chat id 1</chat>
            <chat>chat id 2</chat>
            ...
            </sorted_and_filtered_chat>
            """
        system_message = (
            "You are a codebase expert whose task is to filter and rerank code snippet provided for a user query"
        )

        return UserAndSystemMessages(user_message=user_message, system_message=system_message)

    @classmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[Any]:
        final_data: List[Any] = []
        for response_data in llm_response.content:
            if response_data.type == ContentBlockCategory.TOOL_USE_REQUEST:
                # Skip the tool use request block, as it is not relevant to this prompt
                continue

            chunks_match = re.search(
                r"<sorted_and_filtered_chat>(.*?)</sorted_and_filtered_chat>", response_data.content.text, re.DOTALL
            )
            if chunks_match:
                chunks_content = chunks_match.group(1).strip()
                chat_ids = re.findall(r"<chat>(\d+)</chat>", chunks_content)
                final_data.append({"chat_ids": [int(chat_id) for chat_id in chat_ids]})

        return final_data

    @classmethod
    async def get_parsed_streaming_events(cls, llm_response: StreamingResponse) -> AsyncIterator[BaseModel]:
        raise NotImplementedError("Streaming not supported for this prompt")
