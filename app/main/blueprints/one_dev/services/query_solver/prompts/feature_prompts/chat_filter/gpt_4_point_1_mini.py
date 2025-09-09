import json
from typing import Any, AsyncIterator, Dict, List, Type

from pydantic import BaseModel

from app.backend_common.dataclasses.dataclasses import PromptCategories
from app.main.blueprints.one_dev.services.query_solver.agents.chat_history_handler.dataclasses.main import PreviousChats
from deputydev_core.llm_handler.dataclasses.main import (
    NonStreamingResponse,
    StreamingResponse,
    UserAndSystemMessages,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import (
    ContentBlockCategory,
)
from deputydev_core.llm_handler.providers.openai.prompts.base_prompts.base_gpt_4_point_1_mini import (
    BaseGpt4Point1MiniPrompt,
)
from deputydev_core.utils.app_logger import AppLogger


class SortedAndFilteredChatIDs(BaseModel):
    chat_ids: List[int]


class Gpt4Point1MiniRelevantChatFilterPrompt(BaseGpt4Point1MiniPrompt):
    prompt_type = "CHAT_RE_RANKING"
    prompt_category = PromptCategories.CODE_GENERATION.value

    def __init__(self, params: Dict[str, Any]) -> None:
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
            Please sort and filter the following chat history based on the user's query, so that it can be used as context for an LLM to answer the query.
            <chat_history>
            {self._create_xml_chats(self.params["chats"])}
            </chat_history>
            The user query is as follows -
            <user_query>{self.params.get("query")}</user_query>
            <important>
            Carefully select and prioritize chat entries that are most relevant to the user's query. Retain the context that would help understand the user's intent or provide necessary background for answering the query. If certain chats revolve around a specific topic, function, or issue mentioned in the user query, keep all related chats together.
            Do not be too aggressive in removing chats—ensure that all conversations relevant to the user query are included. Limit the final selection to a maximum of 5 of the most relevant chats.
            </important>
            """
        system_message = "You are an expert in curating conversational history. Your task is to filter, select, and rerank chat messages provided for a user query, ensuring that only the most relevant conversations are retained as context for answering the user's question."
        return UserAndSystemMessages(user_message=user_message, system_message=system_message)

    @classmethod
    def get_text_format(cls) -> Type[BaseModel]:
        """
        Returns the text format for the response.
        """
        return SortedAndFilteredChatIDs

    @classmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[Any]:
        final_data: List[Any] = []
        for response_data in llm_response.content:
            # You may still want to skip tool requests, if that's possible in your data
            if getattr(response_data, "type", None) == ContentBlockCategory.TOOL_USE_REQUEST:
                continue

            try:
                # Parse the JSON string directly from the text attribute
                data = json.loads(response_data.content.text)
                if "chat_ids" in data and isinstance(data["chat_ids"], list):
                    final_data.append({"chat_ids": data["chat_ids"]})
            except json.JSONDecodeError as e:
                AppLogger.log_error(f"Failed to parse JSON from LLM response: {e}")
        return final_data

    @classmethod
    async def get_parsed_streaming_events(cls, llm_response: StreamingResponse) -> AsyncIterator[BaseModel]:
        raise NotImplementedError("Streaming not supported for this prompt")
