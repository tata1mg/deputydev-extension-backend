import json
import textwrap
from typing import Any, List, Type

from pydantic import BaseModel

from app.backend_common.dataclasses.dataclasses import PromptCategories
from app.backend_common.models.dto.message_thread_dto import ContentBlockCategory
from deputydev_core.llm_handler.dataclasses.main import NonStreamingResponse, UserAndSystemMessages
from deputydev_core.llm_handler.providers.openai.prompts.base_prompts.base_gpt_4_point_1_mini import (
    BaseGpt4Point1MiniPrompt,
)
from deputydev_core.utils.app_logger import AppLogger

from ...dataclasses.main import PromptFeatures


class SortedAndFilteredChunksSources(BaseModel):
    chunks_source: List[str]


class Gpt4Point1MiniChunkReRankingPrompt(BaseGpt4Point1MiniPrompt):
    prompt_type = PromptFeatures.CHUNK_RE_RANKING.value
    prompt_category = PromptCategories.CODE_GENERATION.value

    def get_prompt(self) -> UserAndSystemMessages:
        focus_chunks_prompt = (
            textwrap.dedent(f"""
                Here are the chunks explicitly mentioned by the user:
                {self.params.get("focus_chunks")}
            """)
            if self.params.get("focus_chunks")
            else ""
        )

        related_chunks_prompt = textwrap.dedent(f"""
            Here are related chunks from the codebase:
            {self.params.get("related_chunk")}
        """)

        user_message = textwrap.dedent(f"""
            The user query:
            <user_query>{self.params.get("query")}</user_query>

            {focus_chunks_prompt}

            {related_chunks_prompt}

            <important>
            - Keep all the chunks that are relevant to the user query, do not be too forceful in removing out chunks.
            - Do not remove chunks lightly; ensure no relevant chunk is missed.
            </important>

            Please sort and filter the above chunks based on the user's query, and return the result as valid JSON matching the following schema:

            {json.dumps(SortedAndFilteredChunksSources.model_json_schema(), indent=2)}

            Respond with only the JSON object, with key "chunks_source" containing a list of source identifiers. i.e. whatever is inside <source>chunks_source</source>
        """)

        system_message = "You are a codebase expert filtering and reranking code snippets."

        return UserAndSystemMessages(system_message=system_message, user_message=user_message)

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
