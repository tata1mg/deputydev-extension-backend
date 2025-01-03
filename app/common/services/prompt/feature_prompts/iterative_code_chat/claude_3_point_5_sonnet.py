from app.common.services.prompt.llm_base_prompts.claude_3_point_5_sonnet import (
    BaseClaude3Point5SonnetPrompt,
)


class Claude3Point5IterativeCodeChatPrompt(BaseClaude3Point5SonnetPrompt):
    prompt_type = "ITERATIVE_CODE_CHAT"

    def __init__(self, params: dict):
        self.params = params

    def get_prompt(self):
        system_message = """
                You are a code expert, and asked a question by the user. You need to respond to the user query based on the context of the conversation.
                Please generate code snippets, explanations, or any other relevant information to help the user with their query.
                Remember to:
                - Write actual implementation code, not just pseudocode the code can be copied and used directly.
                - Please follow the project's existing code writing pattern.
                - Keep the tests focused and maintainable.
                - Include necessary imports and setup.
                - Use inline comments where ever required for understanding code better.
            """

        user_message = f"""
            Please handle the user query on your last response : {self.params.get('query')}

            Please respond in the following format:
            <response>
            Your response here
            </response>
            <is_task_done>true</is_task_done>
            Please put your entire response within the <response> tag.
            Set the <is_task_done> tag to true if you have responded correctly.
        """

        return {"system_message": system_message, "user_message": user_message}

    @classmethod
    def get_parsed_result(cls, llm_response: str) -> dict:
        final_query_resp = None
        is_task_done = None

        if "<response>" in llm_response:
            final_query_resp = llm_response.split("<response>")[1].split("</response>")[0].strip()
        if "<is_task_done>true</is_task_done>" in llm_response:
            is_task_done = True

        if final_query_resp and is_task_done is not None:
            return {"response": final_query_resp, "is_task_done": is_task_done}
        raise ValueError("Invalid LLM response format. Response not found.")
