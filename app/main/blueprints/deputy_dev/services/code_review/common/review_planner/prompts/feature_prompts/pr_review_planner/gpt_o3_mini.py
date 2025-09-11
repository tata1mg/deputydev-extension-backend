from typing import Any, AsyncIterator, Dict, List

from deputydev_core.llm_handler.dataclasses.main import (
    NonStreamingResponse,
    StreamingResponse,
    UserAndSystemMessages,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import (
    ContentBlockCategory,
    LLModels,
    MessageData,
)
from deputydev_core.llm_handler.prompts.base_prompt import BasePrompt

from app.backend_common.dataclasses.dataclasses import PromptCategories
from app.main.blueprints.deputy_dev.services.code_review.common.review_planner.prompts.dataclasses.main import (
    PromptFeatures,
)


class GptO3MiniReviewPlannerPrompt(BasePrompt):
    prompt_type = PromptFeatures.PR_REVIEW_PLANNER.value
    prompt_category = PromptCategories.CODE_REVIEW.value
    model_name = LLModels.GPT_O3_MINI

    def get_system_prompt(self) -> str:
        system_message = """
        You are an efficient code review planning system. Your job is to create a concise, actionable plan for reviewing PR diffs that maximizes information while minimizing tool usage.
        
        <responsibilities>
        1. ANALYZE THE PR SCOPE:
           - Determine PR size and complexity to right-size the review plan
           - For small PRs, create minimal plans with only essential tool calls
           - For large PRs, prioritize critical changes and high-risk areas
           - Despite of size if you see something critical in PR flag that.
        
        2. IDENTIFY KEY ELEMENTS:
           - List explicitly visible functions/classes/variables from the diff
           - Infer likely important elements not fully visible in the diff
           - Focus only on the most impactful changes (security risks, API changes, etc.)
        
        3. OPTIMIZE TOOL USAGE:
           - Limit total tool calls to 10-15 maximum for any PR size
           - Prioritize high-value tool calls that provide critical context
           - Combine similar searches into single patterns where possible
           - Eliminate redundant or low-value tool calls
        
        4. CREATE A MINIMAL, EFFICIENT PLAN:
           - Default to assuming code is visible and understandable without extra context
           - Only suggest tool calls when critical context is truly missing
           - Focus on security-sensitive areas, API changes, and breaking changes
        </responsibilities>
        
        Tool optimization strategies:
        GREP_SEARCH: Find exact code usages (e.g., functions, variables) across files using content-based pattern matching. Provide exact search term in this, don't provide any symbols in suffix of prefix. like: "get_data_from_db(": This bracket symbol should not be there in keyword.
        FILE_PATH_SEARCHER: Locate files by fuzzy-matching names or list all files in a directory.  useful for locating related components when names are guessed or unclear in the diff
        ITERATIVE_FILE_READER: Read specific line ranges from a file to inspect code or gather context.
        
        Remember: The goal is to provide just enough context for an effective review, not to map the entire codebase. Prioritize clarity and efficiency over comprehensiveness.
        
        Your output should be a precise, step-by-step plan that another AI can follow to conduct an efficient and thorough code review, even with incomplete information.
        """
        return system_message

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = self.get_system_prompt()

        user_message = f"""
        Create a detailed review plan for this Pull Request:

        PR Title: {self.params["PULL_REQUEST_TITLE"]}
        
        PR Description:
        {self.params["PULL_REQUEST_DESCRIPTION"]}
        
        PR Diff:
        {self.params["PULL_REQUEST_DIFF"]}
        
        Focus Area of Agent: 
        {self.params["FOCUS_AREA"]}
        
        Provide a structured plan with these components:
        
        1. **KEY CHANGES SUMMARY** (2-3 sentences)
           - What's the core change in this PR?
           - What's the highest risk element?
           - Identify potential impact scope (local, module, system-wide)
        
        2. **DEPENDENCY MAPPING**
           - For VISIBLE elements, suggest specific grep searches to find usages
           - For INFERRED elements, suggest broader pattern searches that might find them
           - Identify related files that should be examined based on naming patterns and lines window to look for in those files.
           - Propose multiple search strategies when exact names aren't clear
        
        3. **INVESTIGATION SEQUENCE**
           - Provide a brief ordered plan for tool usage
           - Focus on high-risk areas first
           - Explain what decisions to make based on each tool result. Keep it crisp.
        
        4. **FOCUS AREAS**
           - Highlight high-risk changes needing deeper review (max 5-6)
           - Mark elements as [VISIBLE] or [INFERRED]
           - Flag sensitive modifications
           - For each element, note if it's security-sensitive
        
        5. **TOOL USAGE STRATEGY** (5-10 maximum)
           - List specific, optimal tool calls in sequence
           - For each call, explain:
             * What information this call will provide
             * What to look for in the results
             * Follow-up tool calls based on possible findings
        
        IMPORTANT:
        - Clearly distinguish between CERTAIN (explicitly visible) and INFERRED (guessed) elements
        - When suggesting grep searches, provide multiple patterns to increase chances of finding relevant code
        - When function/class names aren't clear from the diff, propose file name pattern searches
        - For each inferred element, provide the reasoning behind your inference
        - Suggest broader context-gathering approaches when the diff shows limited context
        - We have to use limited tools to get the most relevant snippets
        - Small PRs (1-3 files) should have minimal tool calls (3-5 max)
        - Medium PRs (4-10 files) should have moderate tool calls (5-8 max)
        - Large PRs (10+ files) should have focused tool calls (8-10 max)
        
        Remember: Incomplete visibility in the diff is normal. Your job is to create a plan that systematically builds context through smart tool usage, starting with what's known and expanding to what's related.
        """

        return UserAndSystemMessages(system_message=system_message, user_message=user_message)

    @classmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[Dict[str, Any]]:
        final_content: List[Dict[str, Any]] = []

        for content_block in llm_response.content:
            if content_block.type == ContentBlockCategory.TOOL_USE_REQUEST:
                raise NotImplementedError("Tool use request not implemented for this prompt")
            elif content_block.type == ContentBlockCategory.TEXT_BLOCK:
                final_content.append(content_block.content.text)

        return final_content

    @classmethod
    async def get_parsed_streaming_events(cls, llm_response: StreamingResponse) -> AsyncIterator[Any]:
        raise NotImplementedError("Streaming events not supported for this prompt")

    @classmethod
    def get_parsed_response_blocks(cls, response_block: List[MessageData]) -> List[Dict[str, Any]]:
        raise NotImplementedError("This method must be implemented in the child class")
