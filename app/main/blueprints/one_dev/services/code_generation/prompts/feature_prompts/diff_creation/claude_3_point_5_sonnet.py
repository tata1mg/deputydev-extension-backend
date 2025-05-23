import re
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


class Claude3Point5DiffCreationPrompt(BaseClaude3Point5SonnetPromptHandler):
    prompt_type = "DIFF_CREATION"
    prompt_category = PromptCategories.CODE_GENERATION.value

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = """
                You are a senior developer who has a huge amount of experience in applying code diff. You will be given some blocks of code or documentation in the previous conversation
                and you would be asked to get diffs that could be applied to the original codebase and is expected to run without syntactical errors.
            """

        user_message = """
            For all the code you wrote in the conversation with the user, please provide the diff, pr title and commit description that needs to be applied.
            1. Go through each chunk in the initial query and all subsequent queries, and provide a diff for all the final modifications that need to be made on them. The diff chunk should contain the line numbers from original chunk, and the content should be the data those lines should be replaced with.
            2. If a new file needs to be created, provide the diff for the new file as a new chunk of code, with the file path.
            3. Do not use any human understandable lines or comments to signify the diff like "remove existing code", "add new code", etc.
            4. Provide the complete diff without missing any lines.
            5. If the diff is too large, provide the diff in multiple chunks.
            6. Your diff will automatically be applied to the code base, so be extra sure to make sure the existing code that needs to be matched is not altered in any way.

            <response_format>
            Provide the diff in the chunk format like this -
            <all_chunks>
            <chunk source="aa.py" L2:2>
            def foo():
            </chunk>
            <chunk source="bb.py" L5:5>
            return 5
            </chunk>
            </all_chunks>
            <pr_title>Auto apply diff</pr_title>
            <commit_message>Auto apply diff</commit_message>
            </response_format>

            if no diff is needed, provide this response and ignore the above one:
            <response_format>
            <all_chunks></all_chunks>
            <pr_title></pr_title>
            <commit_message></commit_message>
            </response_format>

            <important>
            1. Check line numbers exactly from the source snippets.
            2. Make sure to make the diff chunks as small as possible.
            </important>

            <example>
            For example, if the initial chunk was -
            <chunk source="aa.py:138-147">
            1: # This is a sample code
            2: def foo():
            3:    x = 1
            4:    y = 2
            5:  return x + y
            </chunk>

            If you want to add a line, say m = 20 at line 3, but want to keep the next line, then the diff chunk should be -
            <chunk source="aa.py" L3:3>
            m = 20
            x = 1
            </chunk>

            If you want to replace line 3 with say, m = 20, then the diff chunk should be -
            <chunk source="aa.py" L3:3>
            m = 20
            </chunk>

            If you want to change from line 3 to 5, and add a number of lines between them, then the diff chunk should be -
            <chunk source="aa.py" L3:5>
            m = 20
            x = 1
            y = 2
            z = 3
            k = 4
            return x + y + z + k + m
            </chunk>


            If you want to add a new file, say bb.py, with the following content -
            <chunk source="bb.py" L1:1>
            def bar():
                return 5
            </chunk>

            If you want to change at lines 1, and then 4 to 5, then provide 2 separate chunks like -
            <chunk source="aa.py" L1:1>
            @staticmethod
            def foo():
            </chunk>
            <chunk source="aa.py" L4:5>
            return x
            </chunk>
            </example>

            If a chunk has changes at 2 places, provide it like 2 separate chunks, and change the line numbers accordingly, by checking line numbers from given initial query.
        """

        return UserAndSystemMessages(user_message=user_message, system_message=system_message)

    @classmethod
    def _parse_text_block(cls, text_block: TextBlockData) -> Dict[str, Any]:
        llm_response = text_block.content.text
        # get all chunks from response via regex
        all_chunks_block = re.search(r"<all_chunks>(.*?)</all_chunks>", llm_response, re.DOTALL)

        if not all_chunks_block:
            raise ValueError("No chunks found in the response")

        all_chunks = all_chunks_block.group(1)
        chunks = re.findall(r"<chunk source=\"(.*?)\" L(.*?):(.*?)>(.*?)</chunk>", all_chunks, re.DOTALL)

        # group chunks by file path
        chunks_by_file = {}
        for chunk in chunks:
            file_path = chunk[0]
            start_line = int(chunk[1])
            end_line = int(chunk[2])
            diff = chunk[3]
            chunks_by_file[file_path] = chunks_by_file.get(file_path, []) + [(start_line, end_line, diff)]

        pr_title = re.search(r"<pr_title>(.*?)</pr_title>", llm_response, re.DOTALL)
        if pr_title:
            pr_title = pr_title.group(1)

        commit_message = re.search(r"<commit_message>(.*?)</commit_message>", llm_response, re.DOTALL)
        if commit_message:
            commit_message = commit_message.group(1)

        return {"chunks_by_file": chunks_by_file, "pr_title": pr_title, "commit_message": commit_message}

    @classmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[Dict[str, Any]]:
        final_content: List[Dict[str, Any]] = []

        for content_block in llm_response.content:
            if content_block.type == ContentBlockCategory.TOOL_USE_REQUEST:
                raise NotImplementedError("Tool use request not implemented for this prompt")
            elif content_block.type == ContentBlockCategory.TEXT_BLOCK:
                final_content.append(cls._parse_text_block(content_block))

        return final_content
