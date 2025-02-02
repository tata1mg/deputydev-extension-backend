from app.common.services.prompt.llm_base_prompts.claude_3_point_5_sonnet import (
    BaseClaude3Point5SonnetPrompt,
)


class Claude3Point5DocsGenerationPrompt(BaseClaude3Point5SonnetPrompt):
    prompt_type = "DOCS_GENERATION"

    def __init__(self, params: dict):
        self.params = params

    def get_prompt(self):
        system_message = """
                You are a documentation assistant tasked with generating clear, concise, and informative
                documentation for the provided code. Your role is to analyze the code and its context, and create
                documentation that explains its purpose, behavior, inputs, outputs, and any other relevant details.

                Remember: docstring should be embedded at the correct location in the code.
            """

        user_message = f"""
            Here is the code you need to generate docstrings for:
            {self.params.get("query")}

            Make sure that you do not change the structure of the code or rename anything. Code should not be touched.
            Also, make sure to give out documentation in such a way that in a subsequent prompt, I can generate the diff to be applied on the source code.

        """

        if self.params.get("custom_instructions"):
            user_message += f"""
            Here are some custom instructions for the documentation supplied by the user:
                {self.params.get("custom_instructions")}

        """

        user_message += f"""
            The relevant code chunks in relation to the provided code are as follows:
            {self.params.get("relevant_chunks")}

            Guidelines:
                1. Provide a high-level overview of the code's purpose and functionality.
                2. Describe the inputs (parameters, arguments, configurations) and their roles.
                3. Specify the outputs (return values, generated data, side effects) in detail.
                4. Document any dependencies, preconditions, or external factors influencing the code.
                5. Highlight potential edge cases, error handling, or limitations.
                6. If relevant, include usage examples to enhance clarity and usability.
                7. Follow a consistent and professional format, such as Google style, NumPy style, or reStructuredText.
                8. Ensure the documentation is comprehensive enough for developers to understand and use the code effectively.
                9. If documentation is requested for an entire file, you should provide descriptions for each class and function within the file

            Your goal is to produce documentation that is easy to understand, technically accurate, and useful for developers.

            Provide the response in the following format:

            <response>
            \"\"\"
            Your generated docstring here with code
            \"\"\"
            </response>
            <is_task_done>true</is_task_done>
            <summary>
            Please return a short summary of response. Please include function, classes and files names which are part of response specifically.
            </summary>
            Please put your entire response within the <response> tag.
            Set the <is_task_done> tag to true if the response contains generated docstring.
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
