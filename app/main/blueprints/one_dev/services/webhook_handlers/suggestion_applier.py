from typing import Dict, Optional


class SuggestionsApplier:
    @classmethod
    def get_query_solver_prompt(cls, query: str, relevant_chunks: Optional[str] = None) -> Dict[str, str]:
        system_message = """
            You are a senior developer tasked with improving the AI generated suggestion for a given problem.
            Your role is to carefully analyze the provided code context and user query to refine the generated suggestion.
        """

        user_message = f"""
            User Query: {query}
            """
        if relevant_chunks:
            user_message += f"""
            Additional relevant code context from the repository:
            {relevant_chunks}

            Please provide a helpful and accurate response to my query, taking into account the given code context.

            Please provide the response in the following format:
            <response>
            Your response here
            </response>

            Please put your entire response within the <response> tag.
            """

        prompt = {"system_message": system_message, "user_message": user_message}
        return prompt
