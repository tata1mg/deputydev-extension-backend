from typing import Any, Dict, List

from app.backend_common.dataclasses.dataclasses import PromptCategories
from app.backend_common.models.dto.message_thread_dto import (
    ContentBlockCategory,
    TextBlockData,
)
from app.backend_common.services.llm.dataclasses.main import (
    NonStreamingResponse,
    UserAndSystemMessages,
)
from app.backend_common.services.llm.providers.anthropic.prompts.base_prompts.base_claude_3_point_5_sonnet_prompt_handler import (
    BaseClaude3Point5SonnetPromptHandler,
)


class Claude3Point5TaskPlanGenerationPrompt(BaseClaude3Point5SonnetPromptHandler):
    prompt_type = "TASK_PLANNER"
    prompt_category = PromptCategories.CODE_GENERATION.value

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = """
            You are a task planning assistant designed to analyze code and generate structured,
            actionable plans based on the provided context. Your role is to help break down the user's task into
            clear steps while considering best practices, potential challenges, and ways to optimize the process.
        """

        user_message = f"""
            Relevant Code Context from the existing code in the repository:
            {self.params.get("relevant_chunks")}

            User Query: {self.params.get("query")}

            Your task is to generate an implementation plan to solve the user's query based on the provided code context.

            Guidelines to follow:
            1. Carefully analyze the provided code and context.
            2. Clearly explain the reasoning behind each step in the plan.
            3. Ensure the steps are actionable, logical, and well-structured.
            4. Ask clarifying questions if the provided context is insufficient to create a complete plan.
            5. Identify potential challenges or considerations relevant to the task.
            6. When appropriate, include references to specific parts of the code or context to justify your suggestions.
            7. Aim to be concise, but ensure the plan is comprehensive and easy to follow.
            8. Consider the existing code and generate the plan in a way that aligns with the codebase's structure and style, and make sure creating the plan for only updates that need to be made.
            9. Make the plan easy to read, understand, and implement for the user.
            10. Do not try to go beyond the scope of the requested change.
            11. Point out the locations of the changes which are required.
            12. Do not try to re-implement the existing code.

            <important> try giving minimal or no code, it should seem like plain english text with important keywords like function names, class names, file names etc. </important>

            Please provide a helpful and accurate response to my query, taking into account the given code context.

            Please provide the response in the following format:
            <response>
            Your response here
            </response>

            <summary>
            Please return a short summary of response. Please include function, classes and files names which are part of response specifically.
            </summary>

            <is_task_done>true</is_task_done>
            Please put your entire response within the <response> tag.
            Set the <is_task_done> tag to true if the response contains the generated task plan.
            """

        return UserAndSystemMessages(user_message=user_message, system_message=system_message)

    @classmethod
    def _parse_text_block(cls, text_block: TextBlockData) -> Dict[str, Any]:
        llm_response = text_block.content.text
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

    @classmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[Dict[str, Any]]:
        final_content: List[Dict[str, Any]] = []

        for content_block in llm_response.content:
            if content_block.type == ContentBlockCategory.TOOL_USE_REQUEST:
                raise NotImplementedError("Tool use request not implemented for this prompt")
            elif content_block.type == ContentBlockCategory.TEXT_BLOCK:
                final_content.append(cls._parse_text_block(content_block))

        return final_content
