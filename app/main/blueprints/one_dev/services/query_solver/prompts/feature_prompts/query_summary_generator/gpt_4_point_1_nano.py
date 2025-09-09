import json
from typing import Any, AsyncIterator, Dict, List, Type

from pydantic import BaseModel

from app.backend_common.dataclasses.dataclasses import PromptCategories
from deputydev_core.llm_handler.dataclasses.main import (
    NonStreamingResponse,
    StreamingResponse,
    UserAndSystemMessages,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import (
    ContentBlockCategory,
)
from deputydev_core.llm_handler.providers.openai.prompts.base_prompts.base_gpt_4_point_1_nano import (
    BaseGpt4Point1NanoPrompt,
)
from deputydev_core.utils.app_logger import AppLogger


class QuerySummary(BaseModel):
    summary: str
    success: bool


class Gpt4Point1NanoQuerySummaryGeneratorPrompt(BaseGpt4Point1NanoPrompt):
    prompt_type = "QUERY_SUMMARY_GENERATOR"
    prompt_category = PromptCategories.CODE_GENERATION.value

    def __init__(self, params: Dict[str, Any]) -> None:
        self.params = params

    def get_system_prompt(self) -> str:
        return (
            """You are tasked with generating a summary and task status based on all the query conversation history."""
        )

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = self.get_system_prompt()

        # user query
        user_message = """
        Above is the query conversation history. Based on this, generate a summary of the query and its status.

        The summary will be used to compare or filter for related tasks.

        Guidelines for usage:
        - Keep the `summary` short, clear, and specific (2–4 lines max).
        - Mention what was changed, added, or fixed.
        - Use `success` to indicate whether the task was completed as intended.
        - Only send `success` as `false` if the task was not completed or if there were issues, otherwise always set it to `true`.
        - Do not include follow-up commands or verbose descriptions. It is intended for internal task history, reasoning, and relevance filtering.

        Respond with this schema:

        Output format:
        Respond ONLY with a JSON object following the structure below:
        {{
          "summary": "GENERATED_SUMMARY",
          "success": true
        }}
        """
        return UserAndSystemMessages(
            user_message=user_message,
            system_message=system_message,
        )

    @classmethod
    def get_text_format(cls) -> Type[BaseModel]:
        return QuerySummary

    @classmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[QuerySummary]:
        final_data: List[QuerySummary] = []
        for block in llm_response.content:
            if getattr(block, "type", None) == ContentBlockCategory.TOOL_USE_REQUEST:
                continue
            text = block.content.text.strip()
            try:
                data = json.loads(text)
                result = QuerySummary(**data)
                final_data.append(result)
            except (json.JSONDecodeError, ValueError) as e:
                AppLogger.log_error(f"Failed to parse JSON to QuerySummary: {e}, text: {text}")
        return final_data

    @classmethod
    async def get_parsed_streaming_events(cls, llm_response: StreamingResponse) -> AsyncIterator[BaseModel]:
        raise NotImplementedError(f"Streaming events not implemented for {cls.prompt_type}")
