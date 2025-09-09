import re
from typing import Any, Dict, List

from app.backend_common.dataclasses.dataclasses import PromptCategories
from app.backend_common.models.dto.message_thread_dto import (
    ContentBlockCategory,
    TextBlockData,
)
from deputydev_core.llm_handler.dataclasses.main import (
    NonStreamingResponse,
    UserAndSystemMessages,
)
from deputydev_core.llm_handler.providers.anthropic.prompts.base_prompts.base_claude_3_point_5_sonnet_prompt_handler import (
    BaseClaude3Point5SonnetPromptHandler,
)

from ...dataclasses.main import PromptFeatures


class Claude3Point5ChunkReRankingPrompt(BaseClaude3Point5SonnetPromptHandler):
    prompt_type = PromptFeatures.CHUNK_RE_RANKING.value
    prompt_category = PromptCategories.CODE_GENERATION.value

    def get_prompt(self) -> UserAndSystemMessages:
        focus_chunks_prompt = (
            f"""
            Here are the chunks that are taken from the files/snippets the user has explicitly mentioned:
            {self.params.get("focus_chunks")}
        """
            if self.params.get("focus_chunks")
            else ""
        )

        user_message = f"""
        The user query is as follows -
        <user_query>{self.params.get("query")}</user_query>

        {focus_chunks_prompt}

        Here are the related chunks found by similarity search from the codebase for query
        {self.params.get("related_chunk")}

        <important>
        - Keep all the chunks that are relevant to the user query, do not be too forceful in removing out chunks.
        - We can't miss any relevant chunk, please dual check if u have missed any chunk.
        - Don't return chunks directly from user query. Always return from relevant chunks
          or focus chunks.
        </important>

        Please sort and filter the following chunks based on the user's query. Please return only
        source value included in each chunk.

        <sorted_and_filtered_chunks>
        <source>content1</source>
        <source>content2</source>
        ...
        </sorted_and_filtered_chunks>
        """
        system_message = (
            "You are a codebase expert whose task is to filter and rerank code snippet provided by a user query."
        )

        return UserAndSystemMessages(system_message=system_message, user_message=user_message)

    @classmethod
    def _parse_text_block(cls, text_block: TextBlockData) -> Dict[str, Any]:
        llm_response = text_block.content.text
        chunks_match = re.search(
            r"<sorted_and_filtered_chunks>(.*?)</sorted_and_filtered_chunks>", llm_response, re.DOTALL
        )
        # Now we can safely use group(1) since we confirmed we have a match
        if not chunks_match:
            return {"filtered_chunks": []}
        chunks_content = chunks_match.group(1)

        # Extract source information
        sources = re.findall(r"<source>(.*?)</source>", chunks_content)

        return {"filtered_chunks": sources}

    @classmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[Dict[str, Any]]:
        final_content: List[Dict[str, Any]] = []

        for content_block in llm_response.content:
            if content_block.type == ContentBlockCategory.TOOL_USE_REQUEST:
                raise NotImplementedError("Tool use request not implemented for this prompt")
            elif content_block.type == ContentBlockCategory.TEXT_BLOCK:
                final_content.append(cls._parse_text_block(content_block))

        return final_content
