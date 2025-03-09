from app.backend_common.services.llm.providers.anthropic.prompts.base_prompts.claude_3_point_5_sonnet import (
    BaseClaude3Point5SonnetPrompt,
)


class Claude3Point5TestPlanGenerationPrompt(BaseClaude3Point5SonnetPrompt):
    prompt_type = "TEST_PLAN_GENERATION"

    def __init__(self, params: dict):
        self.params = params

    def get_prompt(self):
        system_message = """
            You are an experienced test engineer specializing in comprehensive test case planning.
            Your goal is to help developers strategically plan test coverage for their code.

            Test Case Planning Approach:
            1. Analyze the code's functionality and requirements thoroughly
            2. Identify key scenarios, including:
               - Normal/happy path scenarios
               - Edge cases
               - Error conditions
               - Boundary conditions
            3. Create a structured test case plan that covers:
               - Different input types
               - Potential failure modes
               - Performance considerations
               - Security implications
            4. Provide a clear rationale for each test case category
            5. Suggest testing strategies and approaches
            6. Highlight potential risks or complex areas needing detailed testing

            Key Planning Principles:
            - Think comprehensively about potential scenarios
            - Prioritize test cases based on risk and impact
            - Consider both functional and non-functional testing needs
            - Provide actionable insights for test implementation
            - Be systematic and methodical in test case planning
        """

        user_message = f"""
            Context for Test Case Planning:
            Here's the selected code snippet for which test cases need to be planned:
            {self.params.get("query")}


            Here are some chunks of code related to the above code taken from the repository:
            {self.params.get("code_context")}

            Develop a comprehensive test case plan with the following deliverables:
            1. Test Scenario Breakdown
               - List key scenarios to test
               - Categorize scenarios (normal cases, edge cases, error cases)
               - Explain rationale for each scenario

            2. Test Case Strategy
               - Recommended testing approach
               - Potential testing techniques (unit, integration, etc.)
               - Suggested testing tools or frameworks

            3. Risk Analysis
               - Identify potential testing challenges
               - Highlight areas requiring special attention
               - Suggest mitigation strategies for complex testing scenarios

            4. Coverage Recommendations
               - Proposed test coverage approach
               - Metrics for assessing test completeness
               - Suggestions for additional testing considerations

            Provide a detailed, structured plan that guides test case development
            without writing the actual test code.

            Please provide your response in this format:
            <response>
            Your test case plan here
            </response>
            <is_task_done>true</is_task_done>

            Set the <is_task_done> tag to true if the response contains the test case plan.
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
