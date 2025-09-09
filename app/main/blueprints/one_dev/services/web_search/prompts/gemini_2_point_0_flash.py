from typing import AsyncIterator, Dict, List

from pydantic import BaseModel

from app.backend_common.dataclasses.dataclasses import PromptCategories
from deputydev_core.llm_handler.dataclasses.main import (
    NonStreamingResponse,
    StreamingResponse,
    UserAndSystemMessages,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import (
    ContentBlockCategory,
    MessageData,
    TextBlockData,
)
from deputydev_core.llm_handler.providers.google.prompts.base_prompts.base_gemini_2_point_0_flash import (
    BaseGemini2Point0FlashPrompt,
)


class Gemini2Point0FlashWebSearch(BaseGemini2Point0FlashPrompt):
    prompt_type = "WEB_SEARCH"
    prompt_category = PromptCategories.CODE_GENERATION.value

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = """
            You are a developer assistant tasked with performing a real-time, AI-powered web search. 
            You will receive a rich, descriptive query that may include code, error messages, technology names, and user goals.
            Use this query to find updated documentation, solutions, or best practices from reliable sources such as official docs, GitHub issues, Stack Overflow, or trusted blogs.
            Always prioritize accuracy, version relevance, and developer applicability.
        """

        user_message = f"""
            {self.params.get("descriptive_query")}
            
            Important:
            - Search should be faster.
        """

        return UserAndSystemMessages(
            user_message=user_message,
            system_message=system_message,
        )

    @classmethod
    def _parse_text_block(cls, text_block: TextBlockData) -> str:
        return text_block.content.text

    @classmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> Dict[str, str]:
        final_content: str = ""
        for content_block in llm_response.content:
            if content_block.type == ContentBlockCategory.TOOL_USE_REQUEST:
                raise NotImplementedError("Tool use request not implemented for this prompt")
            elif content_block.type == ContentBlockCategory.TEXT_BLOCK:
                final_content += content_block.content.text

        return {"web_search_result": final_content}

    @classmethod
    async def get_parsed_streaming_events(cls, llm_response: StreamingResponse) -> AsyncIterator[BaseModel]:
        raise NotImplementedError(f"Streaming events not implemented for {cls.prompt_type}")

    @classmethod
    async def get_parsed_response_blocks(cls, response_block: List[MessageData]) -> List[BaseModel]:
        raise NotImplementedError("This method must be implemented in the child class")
