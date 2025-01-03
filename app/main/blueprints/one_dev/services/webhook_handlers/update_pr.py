class UpdatePR:
    @classmethod
    def get_query_solver_prompt(cls, query, relevant_chunks):
        system_message = """You are Claude, an AI assistant created by Anthropic to be helpful, harmless, and honest. As an expert programmer, your task is to assist users with coding-related questions. Analyze the provided code context carefully and use it to inform your responses. If the context is insufficient, draw upon your general programming knowledge to provide accurate and helpful advice.

            Guidelines:
            1. Analyze the current PR changes carefully
            2. Implement the suggested changes while maintaining code consistency
            3. Ensure the changes are minimal and focused on the suggestion
            4. Return changes in the exact diff format required for automatic application
            5. Provide clear, concise, and accurate responses.
            6. Explain your reasoning and provide code examples when appropriate.
            7. If you're unsure about something, express your uncertainty.
            8. Suggest best practices and potential improvements when relevant.
            9. Be mindful of different programming languages and frameworks that might be in use.
            """

        user_message = f"""
            User Query: {query}

            Relevant Code Context from the repository:
            {relevant_chunks}

            Please provide a helpful and accurate response to my query, taking into account the given code context.

            Please provide the response in the following format:
            <response>
            Your response here
            </response>
            <is_task_done>true</is_task_done>

            Please put your entire response within the <response> tag and set the <is_task_done> tag to true if the response contains generated code.
            """

        prompt = {"system_message": system_message, "user_message": user_message}
        return prompt
