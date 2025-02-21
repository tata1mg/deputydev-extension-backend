import re
from typing import Any, Dict, List

from app.backend_common.services.llm.providers.anthropic.prompts.base_prompts.claude_3_point_5_sonnet import (
    BaseClaude3Point5SonnetPrompt,
)
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.previous_chats.dataclass.main import (
    PreviousChats,
)


class Claude3Point5RelevantChatFilterPrompt(BaseClaude3Point5SonnetPrompt):
    prompt_type = ""

    def __init__(self, params: dict):
        self.params = params

    def get_prompt(self) -> Dict[str, Any]:
        user_message = f"""
            Please sort and filter the following chat history based on the user's query, so that it can be used as a context for a LLM to answer the query.
            <chat_history>
            {self.create_xml_chats(self.params.get("chats"))}
            </chat_history>
            The user query is as follows -
            <user_query>{self.params.get("query")}</user_query>

            <important>
            Please do check and ensure that you keep most of the chunks that are relevant. If one function is selected, keep all chunks related to that function.
            Keep all the chats that are relevant to the user query, do not be too forceful in removing out context
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

        return {"system_message": system_message, "user_message": user_message}

    @classmethod
    def get_parsed_result(cls, llm_response: str) -> Dict[str, List[int]]:
        chunks_match = re.search(r"<sorted_and_filtered_chat>(.*?)</sorted_and_filtered_chat>", llm_response, re.DOTALL)
        chunks_content = chunks_match.group(1).strip()
        chat_ids = re.findall(r"<chat>(\d+)</chat>", chunks_content)
        return {"chat_ids": [int(chat_id) for chat_id in chat_ids]}

    def create_xml_chats(self, previous_chats: List[PreviousChats]) -> str:
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
            xml_output += f"<Query>{chat.query}</Query>"
            xml_output += "</Chat>"

        # Close root element
        xml_output += "</PreviousChatsList>"

        return xml_output
