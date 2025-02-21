from typing import Any, Dict

from app.backend_common.services.llm.providers.anthropic.prompts.base_prompts.claude_3_point_5_sonnet import (
    BaseClaude3Point5SonnetPrompt,
)


class Claude3Point5PlanCodeGenerationPrompt(BaseClaude3Point5SonnetPrompt):
    prompt_type = "PLAN_CODE_GENERATION"

    def __init__(self, params: Dict[str, Any]):
        self.params = params

    def get_prompt(self):
        system_message = """
                You are a code expert, and have created a plan for some code generation task. You are now asked to implement the plan.
            """

        user_message = """
            Please check the previous responses, and take into context the relevant chunks that you heve been provided in the first conversation.
            Now, based on the plan you have previously generated and the chunks you have been provided, please implement the relevant code.

            Please respond in the following format:
            <response>
            Your response here
            </response>
            <summary>
            Please return a short summary of response. Please include function, classes and files names which are part of response specifically.
            </summary>
            <is_task_done>true</is_task_done>
            Please put your entire response within the <response> tag.
            Set the <is_task_done> tag to true if you have responded correctly.
        """

        return {"system_message": system_message, "user_message": user_message}

    @classmethod
    def get_parsed_result(cls, llm_response: str) -> dict:
        final_query_resp = None
        is_task_done = None
        summary = None
        if "<response>" in llm_response:
            final_query_resp = llm_response.split("<response>")[1].split("</response>")[0].strip()
        if "<is_task_done>true</is_task_done>" in llm_response:
            is_task_done = True
        if "<summary>" in llm_response:
            summary = llm_response.split("<summary>")[1].split("</summary>")[0].strip()
        if final_query_resp and is_task_done is not None:
            return {"response": final_query_resp, "is_task_done": is_task_done, "summary": summary}
        raise ValueError("Invalid LLM response format. Response not found.")
