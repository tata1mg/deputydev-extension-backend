import json
from typing import Any, AsyncIterator, Dict, List

from deputydev_core.llm_handler.dataclasses.main import (
    NonStreamingResponse,
    StreamingResponse,
    UserAndSystemMessages,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import MessageData, TextBlockData
from deputydev_core.llm_handler.prompts.llm_base_prompts.gpt_40 import (
    BaseGPT4POINT1Prompt,
)

from app.backend_common.dataclasses.dataclasses import PromptCategories
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.dataclasses.main import PromptFeatures


class GPT4Point1CommentValidationPrompt(BaseGPT4POINT1Prompt):
    prompt_type = PromptFeatures.COMMENT_VALIDATION.value
    prompt_category = PromptCategories.CODE_REVIEW.value
    response_type = "json_object"

    def __init__(self, params: Dict[str, Any]) -> None:
        self.params = params

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = """
            You are an expert code reviewer assisting in validating the relevance and accuracy of code review comments.
            Your task is to rigorously validate whether code review comments are relevant, accurate, and contextually grounded in the PR diff.
            Evaluate each comment against the provided PR diff and relevant code snippets to confirm that they address 
            the changes in a useful and contextually appropriate way. Your goal is to return only genuinely helpful and relevant comments.
        """

        user_message = f"""
        Validate each provided comment's relevance in relation to the code changes shown in the PR diff and relevant code snippets based on following guardrails. 
        and only retain comments that accurately reflect meaningful feedback on the PR code changes.

        Objective:
        - Examine each comment based on the PR diff and the surrounding context provided.
        - If a comment is **not relevant** mark it invalid. Only return comments that accurately highlight a valid concern in the context of the PR diff. Ensure that no relevant feedback is missed.
        - Consider the `bucket` information to ensure that the feedback aligns with the purpose of the agent (e.g., a `security` comment should only address potential security issues).
        - If a comment is made for a change which is already being catered in the PR diff, mark that comment as invalid.
        - If the `corrective_code` and the comment description provided in the comment is already implemented or closely resembles the existing code in the PR diff, mark the comment as invalid.
        - Prioritize correctness over verbosity
        - Keep rationale as the source of truth. It might have some info which might not be visible in PR diff.
        
        ### Review Title Generation:
            - generate a clear, descriptive PR review title (max 15 words) summarizing the key issue fixed in this PR

        ### Input Comments that needs to be validated: 
        ${self.params["COMMENTS"]}

        Below is a sample input structure for the comments you will receive:

        ### Sample Input:

        Comments to Validate:
        [
            {{
                "file_path": "src/app.py",
                "tag": "Suggestion",
                "line_hash": "75fdddd19961586137cae24da95e3514"
                "line_number": 42,
                "comment": "Consider refactoring this function to improve readability.",
                "confidence_score": 0.85,
                "corrective_code": "def my_function(...): pass",
                "buckets": [{{"name": "CODE_MAINTAINABILITY", "agent_id": "c62142f5-3992-476d-9131-bf85e1beffb7"}}],
                "rationale": "X part in the function seems complex",
            }},
            {{
                "file_path": "src/utils.py",
                "tag": "Suggestion",
                "line_hash": "75fdddd19961586137dfd24da95e3514",
                "line_number": 27,
                "comment": "Replace '==' with 'is' for comparison.",
                "confidence_score": 0.92,
                "corrective_code": "if x is None: pass",
                "buckets": [{{"name": "CODE_MAINTAINABILITY", "agent_id": "c62142f5-3992-476d-9131-bf85e1beffb7"}}],
                "rationale": "Reason behind this comment"
            }}
        ]

        ### Format of Output:
        Return only validated comments with the following structure:
        ```JSON
            comments: [{{
            'file_path': '<path of the file on which comment is being made, same as provided in input>',
            'tag': '<Same tag as provided in input>'
            'line_hash': <Same line hash as provided in input>
            'line_number' : <line on which comment is relevant. get this value from `<>` block at each code start in input. Return the exact value present in the input>,
            'comment': '<Same comment as provided in input comment>',
            'corrective_code': '<Corrective code for the comment suggested. Same as provide in input>',
            'is_valid': <boolean value telling whether the comment is actually relevant or not>,
            "buckets": <This is list of buckets [{{"name": <Bucket Name in which the comment falls. Keep it same as given in input comment>, "agent_id": <Id of the agent the comment is given by, Keep it same as given in input comment>}}]>,
            "rationale": <Rationale of agent behind making this comment>
            }}]
            ```

        ###Expected output example 
        ```JSON
        'title': '<A clear, descriptive PR review title (max 15 words) summarizing the key issue fixed in this PR',
        'comments': [
            {{
                "file_path": "src/app.py",
                "tag": "Suggestion",
                "line_hash": "75fdddd19961586137cae24da95e3514"
                "line_number": 42,
                "comment": "Consider refactoring this function to improve readability.",
                "corrective_code": "def my_function(...): pass"
                "is_valid": true,
                "buckets": [{{"name": "CODE_MAINTAINABILITY", "agent_id": "c62142f5-3992-476d-9131-bf85e1beffb7"}}],
                "rationale": "X part in the function seems complex",
            }},
            {{
                "file_path": "src/utils.py",
                "tag": "Suggestion",
                "line_hash": "75fdddd19961586137dfd24da95e3514"
                "line_number": 27,
                "comment": "Replace '==' with 'is' for comparison.",
                "is_valid": false,
                "buckets": [{{"name": "CODE_MAINTAINABILITY", "agent_id": "c62142f5-3992-476d-9131-bf85e1beffb7"}}],
                 "rationale": "Reason behind this comment"
            }}
        ]
        ```

        Validate comments against the PR diff and generate a review title based on the changes:
        <pr_diff>{self.params["PR_DIFF"]}</pr_diff>


        ### Guardrails:
        - Do not remove relevant comments. 
        - NEVER mark a comment as invalid just because it seems minor or stylistic
        - PRESERVE all comments that point to real code issues, even if they're not critical
        - Instruct the LLM to be conservative in discarding comments. It should only remove comments when there's clear evidence of irrelevance based on the context(i.e PR diff, relevant code snippets and content of the comment).
        - Keep all the fields same of a comment as provided in input just add a new key: value pair in each comment. Key as is_valid and its value a boolean which identify the relevancy of comment.
        - Ask the LLM to use the `bucket` tags as an additional validation layer. A comment’s relevance can be double-checked by ensuring it aligns with its `bucket` context (e.g., if it’s tagged as `security`, ensure it specifically addresses security concerns).
        - Any appreciation comments should be marked as invalid
        - All comments should be made on PR diff.
        - In case the comment is related to user story or business validation. Always mark it a valid comment. 
        - Make sure to return response in json_object format only.
        - If the comment refers to a line not present in the PR diff (e.g., the line is unmodified), mark it invalid.
                """

        return UserAndSystemMessages(user_message=user_message, system_message=system_message)

    @classmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[Dict[str, Any]]:
        all_comments: List[Dict[str, Any]] = []
        for response_data in llm_response.content:
            if isinstance(response_data, TextBlockData):
                comments = json.loads(response_data.content.text)
                if comments:
                    all_comments.append(comments)
        return all_comments

    @classmethod
    async def get_parsed_streaming_events(cls, llm_response: StreamingResponse) -> AsyncIterator[Any]:
        raise NotImplementedError("Streaming events not supported for this prompt")

    @classmethod
    def get_parsed_response_blocks(cls, response_block: List[MessageData]) -> List[Dict[str, Any]]:
        raise NotImplementedError("This method must be implemented in the child class")
