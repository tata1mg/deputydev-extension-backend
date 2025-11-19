import re
from typing import Any, Dict, List, Tuple, Union

from deputydev_core.llm_handler.dataclasses.main import NonStreamingResponse, UserAndSystemMessages
from deputydev_core.llm_handler.models.dto.message_thread_dto import (
    ExtendedThinkingData,
    MessageData,
    TextBlockData,
    ToolUseRequestData,
)

from app.backend_common.dataclasses.dataclasses import PromptCategories


class BaseKimiCustomCodeQuerySolverPrompt:
    prompt_type = "CODE_QUERY_SOLVER"
    prompt_category = PromptCategories.CODE_GENERATION.value

    def __init__(self, params: Dict[str, Any]) -> None:
        self.params = params

    def get_system_prompt(self) -> str:
        if self.params.get("write_mode") is True:
            system_message = """
You are DeputyDev, a highly skilled software engineer with deep experience across languages, frameworks, design patterns, and best practices.  
You work in **ACT MODE**, meaning your output is intended to be applied directly to the codebase.

## Communication Guidelines
- Be concise; avoid repetition.
- Use “you” for the user and “I” for yourself.
- Format responses in markdown.
- Focus on solutions rather than apologies.
- Never fabricate information.
- Only output code when it is needed to solve the task.
- Do not mention tools or how you use them; refer to actions in generic terms (e.g. “searching the codebase”, “updating the file”).

## Tool Use (File Editing Model)
You conceptually have two ways of changing files:

### 1. `write_to_file` (full file writes)
Use this when:
- Creating a new file.
- Overwriting or restructuring most or all of a small file.
- Generating boilerplate or templates.

Notes:
- You must provide the full, final content of the file.
- Prefer this only when changes are large; otherwise prefer targeted edits.

### 2. `replace_in_file` (targeted edits)
Use this by default when:
- Updating limited sections of a file.
- Renaming variables, adjusting logic, or editing specific functions/blocks.
- Most of the file should stay unchanged.

Rules:
- Include all changes to a given file in a **single** request when possible.
- If a replace fails, re-read the file and re-run with updated context.
- Add necessary imports/dependencies when needed.

## ACT MODE (Important)
- Assume your changes will be auto-applied.
- Generate complete, coherent changes that can be applied as-is.
- The user should only need to review and approve/reject your changes.

## Code Block Format (for all code output)
Whenever you show code (snippet or patch), use this format:

<code_block>
<programming_language>LANGUAGE_NAME</programming_language>
<file_path>ABSOLUTE/PATH/TO/FILE</file_path>
<is_diff>false</is_diff>
code here
</code_block>

- `programming_language`: e.g. `python`, `typescript`, `go`.
- `file_path`: absolute path for the file the code belongs to.
- `is_diff`:
  - `false` → full file content or standalone snippet.
  - (In ACT mode you may still use non-diff blocks when showing examples or generic code.)

## Editing Files – Additional Rules
- Do **not** use phrases like “existing code”, “previous code here”, etc. in diffs. Patches must be directly applicable.
- When you need to show diffs, treat them as patches that apply cleanly to the current file content.
- Include necessary imports/dependencies in the same patch.

## Task Planning
For **simple** tasks, respond directly without a plan.

For **complex, multi-step** tasks, first output a plan in this format:

<task_plan>
<step>step 1 description<completed>false</completed></step>
<step>step 2 description<completed>false</completed></step>
...
</task_plan>

Then:
- On later turns, update the plan with `<completed>true</completed>` as steps are finished.
- Always update the plan status **before** describing new actions, so the user can track progress.
"""
        else:
            system_message = """
You are DeputyDev, a highly skilled software engineer with deep experience across languages, frameworks, design patterns, and best practices.  
Act as if you are directly talking to the user.


## General Guidelines
- Provide clear, concise, and accurate responses.
- Use “you” for the user and “I” for yourself.
- Maintain a professional but conversational tone.
- Format responses in markdown.
- Never fabricate information.
- If you are unsure, say so and explain what would be needed to be more certain.
- Ask clarifying questions when the task is ambiguous or under-specified (unless the instructions above explicitly say otherwise).
- Consider previous conversations/code snippets only when relevant to the current query.




## Making Code Changes (Advisory Mode)
- Explain **what** to change and **why**, and provide example code when helpful.
- Suggest best practices, patterns, and improvements.
- Be mindful of different languages and frameworks.
- When appropriate, go deep into downstream functions, classes, and data flow to propose robust solutions.
- Do not assume functions/classes exist if you haven’t “seen” them in the provided or searched context.


## Debugging Guidelines
- Focus on root causes, not just suppressing symptoms.
- Propose logs, assertions, or small test functions to isolate issues.
- Explain reasoning so the user understands the diagnosis.

## External APIs and Dependencies
- Suggest appropriate libraries and APIs without needing explicit permission.
- Mention version/compatibility caveats when relevant.
- Remind the user to keep secrets (API keys, tokens) out of source control.

## Code Block Guidelines
Use `<code_block>` tags when you provide code (snippet or patch). There are two types:

1. **Snippets / full file content** (non-diff).
2. **Diff-style patches** (for files in the working repository only).

General structure:

<code_block>
<programming_language>LANGUAGE_NAME</programming_language>
<file_path>ABSOLUTE/PATH/TO/FILE</file_path>
<is_diff>BOOLEAN</is_diff>
code here
</code_block>

### Non-diff code blocks
- `is_diff` = `false`.
- Use for:
  - Self-contained examples.
  - New files when you don’t need to express changes as a diff.
  - Generic code you’re explaining.

### Diff code blocks
If you are confident about the file path and current structure, prefer diffs for actual edits.

- `is_diff` = `true`.
- The content should be a unified diff similar to `diff -U0`:

  - Start with:
    - `--- path/to/file.ext`
    - `+++ path/to/file.ext`
  - For new files:
    - `--- /dev/null`
    - `+++ path/to/new/file.ext`
  - Use `@@ ... @@` hunk headers.
  - Use `-` lines for removed code and `+` lines for added code.
  - Include enough unchanged context lines so the patch applies cleanly.
  - Indentation must be correct.

Rules:
- Do **not** use phrases like “existing code” or “previous code” inside diffs; only include actual code lines.
- When editing a function or block, replace the entire block in one hunk where practical.
- If you move code, use one hunk to remove and another to add.
- Include necessary imports/dependencies when updating a file, but avoid reordering or touching unrelated imports.

## When to Use Diffs vs Snippets
- Use **diffs** when:
  - Editing known files in the working repository.
  - You have enough context to generate a patch that can be applied directly.
- Use **snippets** when:
  - Demonstrating an approach.
  - The file path or exact current content is unclear.
  - Providing generic examples the user will adapt manually.

## Task Planning
For **simple** questions, answer directly.

For **complex** or multi-step tasks, first output a plan:

<task_plan>
<step>step 1 description<completed>false</completed></step>
<step>step 2 description<completed>false</completed></step>
...
</task_plan>

Then:
- Update `<completed>true</completed>` as steps are finished.
- Always update the plan before describing new actions so the user can follow progress.
"""
        return system_message

    def get_prompt(self) -> UserAndSystemMessages:  # noqa: C901
        system_message = self.get_system_prompt()
        user_message = ""
        return UserAndSystemMessages(
            user_message=user_message,
            system_message=system_message,
        )

    @classmethod
    def get_parsed_response_blocks(
        cls, response_block: List[MessageData]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        final_content: List[Dict[str, Any]] = []
        tool_use_map: Dict[str, Any] = {}
        for block in response_block:
            if isinstance(block, TextBlockData):
                final_content.extend(cls._get_parsed_custom_blocks(block.content.text))
            elif isinstance(block, ToolUseRequestData):
                tool_use_request_block = {
                    "type": "TOOL_USE_REQUEST_BLOCK",
                    "content": {
                        "tool_name": block.content.tool_name,
                        "tool_use_id": block.content.tool_use_id,
                        "tool_input_json": block.content.tool_input,
                    },
                }
                final_content.append(tool_use_request_block)
                tool_use_map[block.content.tool_use_id] = tool_use_request_block
            elif isinstance(block, ExtendedThinkingData) and block.content.type == "thinking":
                final_content.append(
                    {
                        "type": "THINKING_BLOCK",
                        "content": {"text": block.content.thinking},
                    }
                )

        return final_content, tool_use_map

    @classmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        final_content: tuple[list[dict[str, Any]], dict[str, Any]]
        final_content = cls.get_parsed_response_blocks(llm_response.content)
        return final_content

    @classmethod
    def _get_parsed_custom_blocks(cls, input_string: str) -> List[Dict[str, Any]]:  # noqa: C901
        result: List[Dict[str, Any]] = []

        # Define the patterns
        thinking_pattern = r"<thinking>(.*?)</thinking>"
        code_block_pattern = r"<code_block>(.*?)</code_block>"
        summary_pattern = r"<summary>(.*?)</summary>"
        task_plan_pattern = r"<task_plan>(.*?)</task_plan>"

        # edge case, check if there is <code_block> tag in the input_string, and if it is not inside any other tag, and there
        # is not ending tag for it, then we append the ending tag for it
        # this is very rare, but can happen if the last block is not closed properly
        last_code_block_tag = input_string.rfind("<code_block>")
        if last_code_block_tag != -1 and input_string[last_code_block_tag:].rfind("</code_block>") == -1:
            input_string += "</code_block>"

        last_summary_tag = input_string.rfind("<summary>")
        if last_summary_tag != -1 and input_string[last_summary_tag:].rfind("</summary>") == -1:
            input_string += "</summary>"

        # for thinking tag, if there is no ending tag, then we just remove the tag, because we can show the thinking block without it
        last_thinking_tag = input_string.rfind("<thinking>")
        if last_thinking_tag != -1 and input_string[last_thinking_tag:].rfind("</thinking>") == -1:
            # remove the last thinking tag
            input_string = input_string[:last_thinking_tag] + input_string[last_thinking_tag + len("<thinking>") :]

        last_task_plan_tag = input_string.rfind("<task_plan>")
        if last_task_plan_tag != -1 and input_string[last_task_plan_tag:].rfind("</task_plan>") == -1:
            input_string += "</task_plan>"

        # Find all occurrences of either pattern
        matches_thinking = re.finditer(thinking_pattern, input_string, re.DOTALL)
        matches_code_block = re.finditer(code_block_pattern, input_string, re.DOTALL)
        matches_summary = re.finditer(summary_pattern, input_string, re.DOTALL)
        matches_task_plan = re.finditer(task_plan_pattern, input_string, re.DOTALL)

        # Combine matches and sort by start position
        matches = list(matches_thinking) + list(matches_code_block) + list(matches_summary) + list(matches_task_plan)
        matches.sort(key=lambda match: match.start())

        last_end = 0
        for match in matches:
            start_index = match.start()
            end_index = match.end()

            if start_index > last_end:
                text_before = input_string[last_end:start_index]
                if text_before.strip():  # Only append if not empty
                    result.append({"type": "TEXT_BLOCK", "content": {"text": text_before.strip()}})

            if match.re.pattern == code_block_pattern:
                code_block_string = match.group(1).strip()
                code_block_info = cls.extract_code_block_info(code_block_string)
                result.append({"type": "CODE_BLOCK", "content": code_block_info})
            elif match.re.pattern == thinking_pattern:
                result.append({"type": "THINKING_BLOCK", "content": {"text": match.group(1).strip()}})
            elif match.re.pattern == task_plan_pattern:
                planning_list = re.findall(r"<step>(.*?)</step>", match.group(1), re.DOTALL)
                plan_steps = [step.strip() for step in planning_list if step.strip()]
                result.append({"type": "TASK_PLAN_BLOCK", "content": {"steps": plan_steps}})

            last_end = end_index

        # Append any remaining text
        if last_end < len(input_string):
            remaining_text = input_string[last_end:]
            if remaining_text.strip():  # Only append if not empty
                result.append({"type": "TEXT_BLOCK", "content": {"text": remaining_text.strip()}})

        return result

    @classmethod
    def extract_code_block_info(cls, code_block_string: str) -> Dict[str, Union[str, bool, int]]:
        # Define the patterns
        language_pattern = r"<programming_language>(.*?)</programming_language>"
        file_path_pattern = r"<file_path>(.*?)</file_path>"
        is_diff_pattern = r"<is_diff>(.*?)</is_diff>"

        # Extract language and file path
        language_match = re.search(language_pattern, code_block_string)
        file_path_match = re.search(file_path_pattern, code_block_string)
        is_diff_match = re.search(is_diff_pattern, code_block_string)

        is_diff = is_diff_match.group(1).strip() == "true"

        language = language_match.group(1) if language_match else ""
        file_path = file_path_match.group(1) if file_path_match else ""

        # Extract code
        code = (
            code_block_string.replace(language_match.group(0), "")
            .replace(file_path_match.group(0), "")
            .replace(is_diff_match.group(0), "")
            .lstrip("\n\r")
        )

        diff = ""
        added_lines = 0
        removed_lines = 0

        if is_diff:
            code_selected_lines: List[str] = []
            code_lines = code.split("\n")

            for line in code_lines:
                if line.startswith(" ") or line.startswith("+") and not line.startswith("++"):
                    code_selected_lines.append(line[1:])
                if line.startswith("+"):
                    added_lines += 1
                elif line.startswith("-"):
                    removed_lines += 1

            code = "\n".join(code_selected_lines)
            diff = "\n".join(code_lines)

        return (
            {
                "language": language,
                "file_path": file_path,
                "code": code,
                "is_diff": is_diff,
            }
            if not is_diff
            else {
                "language": language,
                "file_path": file_path,
                "code": code,
                "diff": diff,
                "is_diff": is_diff,
                "added_lines": added_lines,
                "removed_lines": removed_lines,
            }
        )
