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
from deputydev_core.llm_handler.providers.anthropic.prompts.base_prompts.base_claude_3_point_7_sonnet_prompt_handler import (
    BaseClaude3Point7SonnetPromptHandler,
)
from pydantic import BaseModel

from app.backend_common.dataclasses.dataclasses import PromptCategories


class Claude3Point7UserQueryEnhancerPrompt(BaseClaude3Point7SonnetPromptHandler):
    prompt_type = "USER_QUERY_ENHANCER"
    prompt_category = PromptCategories.CODE_GENERATION.value

    def __init__(self, params: Dict[str, Any]) -> None:
        self.params = params

    def get_system_prompt(self) -> Optional[str]:
        return "Generate an enhanced version of this prompt (reply with only the enhanced prompt - no conversation, explanations, lead-in, bullet points, placeholders, or surrounding quotes). If prompt have URL, include the URL in the enhanced prompt."

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = self.get_system_prompt()

        user_message = f"""
        Prompt: {self.params.get("query")}
        Respond with:
        <enhanced_prompt>
        new enhanced prompt here
        </enhanced_prompt>
        """

        return UserAndSystemMessages(user_message=user_message, system_message=system_message)

    @classmethod
    def _parse_text_block(cls, text_block: TextBlockData) -> Optional[Dict[str, Any]]:
        content = text_block.content.text
        start_tag = "<enhanced_prompt>"
        end_tag = "</enhanced_prompt>"

        if start_tag in content and end_tag in content:
            try:
                enhanced_query = content.split(start_tag)[1].split(end_tag)[0].strip()
                if enhanced_query:
                    return {"enhanced_prompt": enhanced_query}
            except IndexError:
                return None
        return None

    @classmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[Dict[str, Any]]:
        final_content: List[Dict[str, Any]] = []

        for content_block in llm_response.content:
            if content_block.type == ContentBlockCategory.TOOL_USE_REQUEST:
                raise NotImplementedError("Tool use request not implemented for this prompt")
            elif content_block.type == ContentBlockCategory.TEXT_BLOCK:
                parsed_text_block = cls._parse_text_block(content_block)
                if parsed_text_block:
                    final_content.append(parsed_text_block)
        return final_content

    @classmethod
    async def get_parsed_streaming_events(cls, llm_response: StreamingResponse) -> AsyncIterator[BaseModel]:
        raise NotImplementedError(f"Streaming events not implemented for {cls.prompt_type}")
