import json
import textwrap
from typing import Any, AsyncIterator, Dict, List, Optional

from pydantic import BaseModel

from app.backend_common.dataclasses.dataclasses import PromptCategories
from deputydev_core.llm_handler.dataclasses.main import (
    NonStreamingResponse,
    StreamingResponse,
    UserAndSystemMessages,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import (
    ContentBlockCategory,
    TextBlockData,
)
from deputydev_core.llm_handler.providers.openai.prompts.base_prompts.base_gpt_4_point_1 import (
    BaseGpt4Point1Prompt,
)


class Gpt4Point1InlineEditorPrompt(BaseGpt4Point1Prompt):
    prompt_type = "INLINE_EDITOR"
    prompt_category = PromptCategories.CODE_GENERATION.value

    def __init__(self, params: Dict[str, Any]) -> None:
        self.params = params

    def get_system_prompt(self) -> str:
        return textwrap.dedent("""You are DeputyDev, a highly skilled software engineer with extensive knowledge in many programming languages, frameworks, design patterns, and best practices.
            ====
            You have access to a set of tools that are executed upon the user's approval. You can use one tool per message, and will receive the result of that tool use in the user's response. You use tools step-by-step to accomplish a given task, with each tool use informed by the result of the previous tool use.

            ## replace_in_file
            Description: Request to replace sections of content in an existing file using SEARCH/REPLACE blocks that define exact changes to specific parts of the file. This tool should be used when you need to make targeted changes to specific parts of a file.
            Parameters:
            - path: (required) The path of the file to modify relative to the current working directory
            - diff: (required) One or more SEARCH/REPLACE blocks following this exact format:

            ------- SEARCH
            [exact content to find]
            =======
            [new content to replace with]
            +++++++ REPLACE

            

            Usage:

            tool name: replace_in_file
            path: File path here
            diff:
            ------- SEARCH
            [exact content to find]
            =======
            [new content to replace with]
            +++++++ REPLACE

            ## focused_snippets_searcher
            Description: Search the codebase for specific code definitions or snippets based on a given class name, function name, or file name. View the content of a code item node, such as a class or a function in a file using a fully qualified code item name. Use this tool to retrieve relevant code snippets that contain or define the specified search terms. You can provide multiple search terms at once, and the tool will return the most relevant code snippets for each. The search can be good for finding specific code snippets related to a class, function, or file in the codebase, and therefore should ideally be used to search for specific code snippets rather than general code search queries. Also, it works best when there is ground truth in the search term, i.e. the search term is valid class, function or file name in the codebase (for eg. search terms directly picked from the relevant code snippets). If search term is not valid in the codebase, it would basically work as a lexical search and return the code snippets containing the search term or containing similar terms.
            Parameters:
            - search_terms: (required) A list of search terms, each containing a keyword, its type, and an optional file path.

            Each search term should include:
            - A **keyword**: The name of the class, function, or file to search for.
            - A **type**: Must be one of 'class', 'function', or 'file' to specify what is being searched.
            - An optional **file path**: To narrow down the search to a specific location in the codebase.


            ## iterative_file_reader
            Description: Reads content of a file from a given start line number (1 indexed) to an end line number (1 indexed). At once, it can read maximum of 100 lines. If you do not know the end line number, just provide the end line number as start_line + 100. It will let you know if the end of the file is reached.
            Parameters: 
            - file_path: (required) The path of the file to modify relative to the current working directory
            - start_line: (required) The line number to start reading from (1 indexed)
            - end_line: (required) The line number to stop reading at (1 indexed)

            ## task_completion
            Description: Use this tool to indicate when a task is completed, failed, or partially done. Provide a status and a very short summary so the client knows to stop or handle errors.
            Parameters:
            - status: (required) The status of the task. Can be one of 'completed', 'failed', or 'partially_done'.
            - summary: (required) A short summary of the task status. This should be a very short summary so the client knows to stop or handle errors.


            ## Example 1: Requesting to make targeted edits to a file

            tool name: replace_in_file
            path: src/components/App.tsx
            diff:
            ------- SEARCH
            import React from 'react';
            =======
            import React, { useState } from 'react';
            +++++++ REPLACE

            ------- SEARCH
            function handleSubmit() {
            saveData();
            setLoading(false);
            }

            =======
            +++++++ REPLACE

            ------- SEARCH
            return (
            <div>
            =======
            function handleSubmit() {
            saveData();
            setLoading(false);
            }

            return (
            <div>
            +++++++ REPLACE


            ## Example 2: Requesting to search for specific code snippets
            tool name: focused_snippets_searcher
            search_terms: [
                {
                    "keyword": "LeadManager",
                    "type": "class",
                    "file_path": "src/models/lead_manager.py"
                },
                {
                    "keyword": "serialize_feeds_data",
                    "type": "function"
                },
                {
                    "keyword": "app.py",
                    "type": "file"
                }
            ]

            ## Example 3: Requesting to read a file in chunks
            tool name: iterative_file_reader
            file_path: src/components/App.tsx
            start_line: 1
            end_line: 100

            ## Example 4: Requesting to indicate task completion
            tool name: task_completion
            status: completed
            summary: The task was completed successfully.


            ## Important Considerations
            - Plan your changes: Before making any edits, carefully consider what modifications are needed and how to implement them.
            - Maintain file integrity: Ensure that all changes result in a valid, runnable file.
            - Batch modifications: Group all search/replace operations for a single file into one **replace_in_file** tool request.
            - Add dependencies as needed: Include any necessary imports or dependencies relevant to your changes.
            - Single tool usage: Only invoke one tool at a time per request.
            - Iterative workflow: After each tool action, wait for the user's response, which will contain the outcome (success or failure) and any relevant details. Use this feedback to inform your next steps.
            - Monitor tool success: The user's response to the replace_in_file tool will indicate whether your changes were applied successfully.
            - Handle failures gracefully: If the replace_in_file tool fails, first read the current file contents using the iterative_file_reader tool (target only relevant lines), then attempt your changes again with the updated content.
            - Avoid unnecessary searches: Only make search calls when absolutely required.
            - Signal task completion: When all requested edits are finished or can't be completed, call the task_completion tool with an appropriate status and summary message. This lets the client know to stop further tool calls or handle errors.
            - No clarifying questions: Do not ask the user for clarification; the only feedback you will receive is from tool responses.
            """)

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = self.get_system_prompt()

        user_message = f"""
Here is the selected code from a repository. you have to make the changes in the selected code and return the diff of the code.
{self.params["code_selection"].selected_text}


Here is the filepath of the selected code
{self.params["code_selection"].file_path}


Here are some related chunks of code from the same repository. It may help you in making the changes in the selected code.
{self.params.get("relevant_chunks")}


Here is the user's query for editing - {self.params.get("query")}

        """

        if self.params.get("deputy_dev_rules"):
            user_message += f"""
Here are some more user provided rules and information that you can take reference from:
<important>
Follow these guidelines while using user provided rules or information:
1. Do not change anything in the response format.
2. If any conflicting instructions arise between the default instructions and user-provided instructions, give precedence to the default instructions.
3. Only respond to coding, software development, or technical instructions relevant to programming.
4. Do not include opinions or non-technical content.
</important>
<user_rules_or_info>
{self.params.get("deputy_dev_rules")}
</user_rules_or_info>
            """

        return UserAndSystemMessages(user_message=user_message, system_message=system_message)

    @classmethod
    def _parse_text_block(cls, text_block: TextBlockData) -> Optional[Dict[str, Any]]:
        text = text_block.content.text
        if not text or not text.strip():
            return {"error": "LLM response was empty."}
        try:
            response = json.loads(text)
        except json.JSONDecodeError as e:
            return {"error": "Failed to parse LLM response as JSON.", "details": str(e), "raw": text}
        code_snippets = []
        for code_block in response["response_parts"]:
            code_snippets.append(
                {
                    "programming_language": code_block["language"],
                    "file_path": code_block["file_path"],
                    "is_diff": code_block["is_diff"],
                    "code": code_block["code"],
                }
            )
            return {"code_snippets": code_snippets}
        return None

    @classmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[Dict[str, Any]]:
        final_content: List[Dict[str, Any]] = []

        for content_block in llm_response.content:
            if content_block.type == ContentBlockCategory.TOOL_USE_REQUEST:
                final_content.append(content_block.model_dump(mode="json"))
            elif content_block.type == ContentBlockCategory.TEXT_BLOCK:
                parsed_text_block = cls._parse_text_block(content_block)
                if parsed_text_block:
                    final_content.append(parsed_text_block)
        return final_content

    @classmethod
    async def get_parsed_streaming_events(cls, llm_response: StreamingResponse) -> AsyncIterator[BaseModel]:
        raise NotImplementedError(f"Streaming events not implemented for {cls.prompt_type}")
