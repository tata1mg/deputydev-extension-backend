import json
from typing import Any, List, Type

from deputydev_core.llm_handler.dataclasses.main import NonStreamingResponse, UserAndSystemMessages
from deputydev_core.llm_handler.models.dto.message_thread_dto import ContentBlockCategory
from deputydev_core.llm_handler.providers.openai.prompts.base_prompts.base_gpt_4_point_1_mini import (
    BaseGpt4Point1MiniPrompt,
)
from deputydev_core.utils.app_logger import AppLogger
from pydantic import BaseModel

from app.backend_common.dataclasses.dataclasses import PromptCategories

from ...dataclasses.main import PromptFeatures


class SortedAndFilteredChunksSources(BaseModel):
    chunks_source: List[str]


class Gpt4Point1MiniChunkReRankingPrompt(BaseGpt4Point1MiniPrompt):
    prompt_type = PromptFeatures.CHUNK_RE_RANKING.value
    prompt_category = PromptCategories.CODE_GENERATION.value

    def get_prompt(self) -> UserAndSystemMessages:
        """
        Construct a structured prompt for reranking and filtering semantically retrieved code chunks
        based on user query intent and reasoning.
        """

        # Construct user message clearly and consistently
        user_message = f"""
You are assisting in improving semantic retrieval by filtering and ranking codebase chunks.

The user query reasoning or intent (helps you understand semantic context):
<explanation>
{self.params.get("query")}
</explanation>

Here are semantically retrieved chunks from the codebase:
<relevant_chunks>
{self.params.get("relevant_chunks")}
</relevant_chunks>

<important_instructions>
- Keep all chunks that are relevant to the user query and reasoning.
- Do not remove chunks lightly — prefer recall over precision.
- Ensure no relevant chunk is missed.
- Output must be valid JSON following this schema:
{json.dumps(SortedAndFilteredChunksSources.model_json_schema(), indent=2)}
</important_instructions>

Return **only** a JSON object with the key `"chunks_source"` containing a list of selected source identifiers.
"""

        system_message = (
            "You are a highly skilled codebase expert. Your goal is to filter and rerank semantically "
            "retrieved code chunks based on the reasoning and intent behind the user query."
        )

        return UserAndSystemMessages(
            system_message=system_message,
            user_message=user_message.strip(),
        )

    @classmethod
    def get_text_format(cls) -> Type[BaseModel]:
        return SortedAndFilteredChunksSources

    @classmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[Any]:
        final_data: List[Any] = []
        for block in llm_response.content:
            if getattr(block, "type", None) == ContentBlockCategory.TOOL_USE_REQUEST:
                continue
            text = block.content.text.strip()
            try:
                data = json.loads(text)
                if isinstance(data.get("chunks_source"), list):
                    final_data.append({"chunks_source": data["chunks_source"]})
            except json.JSONDecodeError as e:
                AppLogger.log_error(f"Failed to parse JSON from LLM response: {e}, text: {text}")
        return final_data
