import re

from app.backend_common.services.llm.prompts.llm_base_prompts.claude_3_point_5_sonnet import (
    BaseClaude3Point5SonnetPrompt,
)


class Claude3Point5ChunkReRankingPrompt(BaseClaude3Point5SonnetPrompt):
    prompt_type = "CHUNK_RE_RANKING"

    def __init__(self, params: dict):
        self.params = params

    def get_prompt(self):
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

        return {"system_message": system_message, "user_message": user_message}

    @classmethod
    def get_parsed_result(cls, llm_response: str) -> dict:
        chunks_match = re.search(
            r"<sorted_and_filtered_chunks>(.*?)</sorted_and_filtered_chunks>", llm_response, re.DOTALL
        )
        # Now we can safely use group(1) since we confirmed we have a match
        chunks_content = chunks_match.group(1)

        # Extract source information
        sources = re.findall(r"<source>(.*?)</source>", chunks_content)

        return {"filtered_chunks": sources}
