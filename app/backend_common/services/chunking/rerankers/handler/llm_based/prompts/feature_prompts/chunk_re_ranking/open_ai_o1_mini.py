# import re

# from app.backend_common.models.dto.message_thread_dto import LLModels
# from app.backend_common.services.llm.prompts.llm_base_prompts.gpt_4o import (
#     BaseGPT4OPrompt,
# )


# class OpenAIO1MiniPrompt(BaseGPT4OPrompt):
#     model_name = LLModels.GPT_40_MINI
#     prompt_type = "CHUNK_RE_RANKING"

#     def __init__(self, params: dict):
#         self.params = params

#     def get_prompt(self):
#         focus_chunks_prompt = (
#             f"""
#             Here are the chunks that are taken from the files/snippets the user has explicitly mentioned:
#             {self.params.get("focus_chunks")}
#         """
#             if self.params.get("focus_chunks")
#             else ""
#         )

#         user_message = f"""
#         Please sort and filter the following chunks based on the user's query, so that it can be used as a context for a LLM to answer the query.
#         The user query is as follows -
#         <user_query>{self.params.get("query")}</user_query>

#         <important>
#         Please do check and ensure that you keep most of the chunks that are relevant. If one function is selected, keep all chunks related to that function.
#         </important>

#         {focus_chunks_prompt}

#         Here are the related chunks found by similarity search from the codebase:
#         {self.params.get("related_chunk")}

#         Please send the sorted and filtered chunks in the following format:
#         <important> Keep all the chunks that are relevant to the user query, do not be too forceful in removing out context</important>
#         Please preserve line numbers, source and other metadata of the chunks passed.
#         <sorted_and_filtered_chunks>
#         <chunk>content1</chunk>
#         <chunk>content2</chunk>
#         ...
#         </sorted_and_filtered_chunks>
#         """
#         system_message = (
#             "You are a codebase expert whose task is to filter" " and rerank code snippet provided for a user query"
#         )

#         return {"system_message": system_message, "user_message": user_message}

#     @classmethod
#     def get_parsed_result(cls, llm_response: str) -> dict:
#         chunks_match = re.search(
#             r"<sorted_and_filtered_chunks>(.*?)</sorted_and_filtered_chunks>", llm_response, re.DOTALL
#         )
#         chunks_content = chunks_match.group(1).strip()
#         return {"filtered_chunks": chunks_content}
