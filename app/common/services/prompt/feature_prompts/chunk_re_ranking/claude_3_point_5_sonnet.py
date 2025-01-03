import re

from app.common.services.prompt.llm_base_prompts.claude_3_point_5_sonnet import (
    BaseClaude3Point5SonnetPrompt,
)


class Claude3Point5ChunkReRankingPrompt(BaseClaude3Point5SonnetPrompt):
    prompt_type = "CHUNK_RE_RANKING"

    def __init__(self, params: dict):
        self.params = params

    def get_prompt(self):
        user_message = f"""
        Please sort and filter the following chunks based on the user's query, so that it can be used as a context for a LLM to answer the query.
        The user query is as follows -
        <user_query>{self.params.get("query")}</user_query>

        <important>Please do check and ensure that you keep most of the chunks that are relevant. If one function is selected, keep all chunks related to that function.</important>

        Here are the chunks that are taken from the files/snippets the user has explicitly mentioned:
        {self.params.get("focus_chunks")}
        Here are the related chunks found by similarity search from the codebase:
        {self.params.get("related_chunk")}

        Please send the sorted and filtered chunks in the following format:
        <important> Keep all the chunks that are relevant to the user query, do not be too forceful in removing out context</important>
        Please preserve line numbers, source and other metadata of the chunks passed.
        <sorted_and_filtered_chunks>
        <chunk>content1</chunk>
        <chunk>content2</chunk>
        ...
        </sorted_and_filtered_chunks>
        """
        system_message = "You are a codebase expert"

        return {"system_message": system_message, "user_message": user_message}

    @classmethod
    def get_parsed_result(cls, llm_response: str) -> dict:
        chunks_match = re.search(
            r"<sorted_and_filtered_chunks>(.*?)</sorted_and_filtered_chunks>", llm_response, re.DOTALL
        )
        chunks_content = chunks_match.group(1).strip()
        return {"filtered_chunks": chunks_content}
