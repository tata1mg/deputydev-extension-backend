from typing import Any, AsyncIterator, Dict, List, Optional

from deputydev_core.llm_handler.dataclasses.main import (
    NonStreamingResponse,
    StreamingResponse,
    UserAndSystemMessages,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import (
    ContentBlockCategory,
    TextBlockData,
)
from deputydev_core.llm_handler.providers.google.prompts.base_prompts.base_gemini_2_point_5_flash_prompt_handler import (
    BaseGemini2Point5FlashPromptHandler,
)
from pydantic import BaseModel

from app.backend_common.dataclasses.dataclasses import PromptCategories


class Gemini2Point5FlashLiteQuerySummaryGeneratorPrompt(BaseGemini2Point5FlashPromptHandler):
    prompt_type = "QUERY_SUMMARY_GENERATOR"
    prompt_category = PromptCategories.CODE_GENERATION.value

    def __init__(self, params: Dict[str, Any]) -> None:
        self.params = params

    def get_system_prompt(self) -> str:
        return """
            You are tasked with generating a summary based on all the query conversation history.
        """

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = self.get_system_prompt()

        # user query
        user_message = """
        Above is the query conversation history. Based on this, generate a summary of the query.

        The summary will be used to compare or filter for related tasks.

        Guidelines for usage:
        - Keep the `summary` short, clear, and specific (2–4 lines max).
        - Mention what was changed, added, or fixed.
        - Do not include follow-up commands or verbose descriptions. It is intended for internal task history, reasoning, and relevance filtering.

        Respond with this schema:

        Output format:

        """
        summarization_prompt = """
            Send the response in the following format:
            <summary>
                Your summary here
            </summary>
        """

        return UserAndSystemMessages(
            user_message=user_message + summarization_prompt,
            system_message=system_message,
        )

    @classmethod
    def _parse_text_block(cls, text_block: TextBlockData) -> Dict[str, Any]:
        summary: Optional[str] = None
        if "<summary>" in text_block.content.text:
            summary = text_block.content.text.split("<summary>")[1].split("</summary>")[0].strip()

        if summary:
            return {"summary": summary}
        raise ValueError("Invalid LLM response format. Summary not found.")

    @classmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[Dict[str, Any]]:
        final_content: List[Dict[str, Any]] = []

        for content_block in llm_response.content:
            if content_block.type == ContentBlockCategory.TOOL_USE_REQUEST:
                raise NotImplementedError("Tool use request not implemented for this prompt")
            elif content_block.type == ContentBlockCategory.TEXT_BLOCK:
                final_content.append(cls._parse_text_block(content_block))

        return final_content

    @classmethod
    async def get_parsed_streaming_events(cls, llm_response: StreamingResponse) -> AsyncIterator[BaseModel]:
        raise NotImplementedError(f"Streaming events not implemented for {cls.prompt_type}")
