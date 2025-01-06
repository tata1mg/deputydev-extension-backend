from app.common.services.prompt.llm_base_prompts.claude_3_point_5_sonnet import (
    BaseClaude3Point5SonnetPrompt,
)


class Claude3Point5TestCaseGenerationPrompt(BaseClaude3Point5SonnetPrompt):
    prompt_type = "TEST_CASE_GENERATION"

    def __init__(self, params: dict):
        self.params = params

    def get_prompt(self):
        system_message = """
            You are an experienced test engineer who writes practical, effective test cases. Your role is to help developers
            write specific test cases for their code, focusing on their immediate testing needs while following best practices.

            Approach each test case request as a programmer would:
            1. First understand what specific functionality needs to be tested.
            2. Consider the testing framework and tools available in the codebase.
            3. Write clear, practical test cases that another developer could immediately use.
            4. Include necessary imports, mocks, and setup code.
            5. Use realistic test data and meaningful assertions.
            6. Add helpful comments explaining any complex logic or edge cases.
            7. If test cases asked by user is already written anywhere in code please highlight and improve that only
            with using same test framework and mock pattern used by users.
            8. User can ask to fix the some already generated test cases please check and fix that.
            9. Follow standard unit testing conventions.
            10. Handle dependencies and mocking appropriately.
            11. Add brief comments explaining the test strategy
            12. Follow the project's existing testing patterns and style.

            Remember to:
            - Write actual implementation code, not just pseudocode the code can be copied and used directly.
            - Please follow the project's existing code writing pattern.
            - Include necessary imports and setup.
            - Use inline comments where ever required for understanding code better.
        """

        user_message = f"""
            Here's the selected piece of code for which test case needs to be written:
            {self.params.get("query")}

        """

        if self.params.get("custom_instructions"):
            user_message += f"""
            Here are some custom instructions for the test case supplied by the user:
            {self.params.get("custom_instructions")}

        """

        user_message += f"""
            Here are some chunks of code related to the above code taken from the repository:
            {self.params.get("relevant_chunks")}

            <important> Write test cases for the selected code only. Do not try to add your own methods/functions. </important>

            Write practical test cases for the selection, following these guidelines:

            Please provide your response in this format:
            <response>
            ```python
            # Test implementation here, including imports and any necessary setup
            ```
            </response>
            <is_task_done>true</is_task_done>

            Set the <is_task_done> tag to true if the response contains the generated test cases.
            """

        return {"system_message": system_message, "user_message": user_message}

    @classmethod
    def get_parsed_result(cls, llm_response: str) -> dict:
        final_query_resp = None
        is_task_done = None

        print("LLM Response: ", llm_response)

        if "<response>" in llm_response:
            final_query_resp = llm_response.split("<response>")[1].split("</response>")[0].strip()
        if "<is_task_done>true</is_task_done>" in llm_response:
            is_task_done = True

        if final_query_resp and is_task_done is not None:
            return {"response": final_query_resp, "is_task_done": is_task_done}
        raise ValueError("Invalid LLM response format. Response not found.")
