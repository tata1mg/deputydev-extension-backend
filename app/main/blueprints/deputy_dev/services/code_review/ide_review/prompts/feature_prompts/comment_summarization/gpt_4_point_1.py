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


class GPT4Point1CommentSummarizationPrompt(BaseGPT4POINT1Prompt):
    prompt_type = PromptFeatures.COMMENT_SUMMARIZATION.value
    prompt_category = PromptCategories.CODE_REVIEW.value
    response_type = "json_object"

    def __init__(self, params: Dict[str, Any]) -> None:
        self.params = params

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = """
            You are an expert code reviewer responsible for summarizing and consolidating multiple code review comments on the same line of code into clear, actionable feedback.
        """

        user_message = f"""
            You are acting as an Comments Reviewer for a Pull Request (PR). You will be given with a list of comments that are made on single line in a file, your job is to validate, filter, and summarize the feedback comments provided by multiple specialized agents. Your task involves:

            ###Context:
            - You have access to the PR diff provided below. Carefully review this diff to understand the changes in the code.
            - You will be given a list of comments object. Where each comment object consists of list of comments that are made on that particular line in that file.
            Each of those multiple comment has a comment, a bucket assigned to it, and a corrective code snippet attached to it. 
            - Each comment is tagged with its relevant `bucket` (such as `security`, `code communication`, `algorithm efficiency`) to indicate the type of feedback. Use this metadata to understand the context of each comment.
            - Multiple comments might reference the same line of code, but they come from different agents focusing on various aspects of the code.

            Objective:

            1. **Comment Merging**:
            - When multiple comments on a single line have similar semantic meanings, intelligently merge them to avoid redundancy. Follow these rules:
                - **Same Function or Variable Context**: If comments reference the same function or line context (e.g., missing docstrings, type hints, or complex logic), consolidate them into one summarized bullet.
                - **Unique Comments in Separate Bullets**: If every comment is semantically unique on a line and cannot be clubbed with another bucket comment, create a separate bullet point for each unique comment.
                - **Single Bullet for Uniform Meaning**: If all comments have the same semantic meaning, combine them into one summary bullet, choosing the most relevant bucket name and make sure agent_id is also selected according to bucket.
                - **Separate Bullets for Mixed Meanings**: If there are subsets of comments with shared meanings, group each subset under a bullet with the most relevant bucket name, using concise language to avoid duplication.
            - Preserve the integrity of all individual bucket values in the input data, but make the output summary concise and grouped based on semantic similarity and don't loose actual context of comment.

            2. **Bucket-wise Summary**:
            - Begin each bullet point with the relevant bucket name, followed by a combined summary. If multiple buckets are present, select the most contextually suitable bucket for the combined comment.
            - Maintain bullet format per bucket in the output to ensure clear organization.
            - Ensure that the `buckets` field in the output contains only the buckets used in the summarized comments. Select only the most relevant bucket for bullets where multiple comments were merged, and ensure accuracy in spelling and formatting to match the input.

            3. **Corrective Code Union**:
            - Consolidate all corrective code snippets provided, combining relevant parts to form a unified corrective code block that addresses all feedback. Ensure the corrective code retains functionality and addresses issues highlighted by all buckets.

            4. **Rationale Union**:
            - Consolidate multiple rationale into a single rationale .


            ### Guidelines:
            - Combine related feedback intelligently while preserving important details.
            - Use information from all buckets and comments to create a summary that incorporates the relevant feedback from each perspective.
            - Prioritize feedback based on severity and impact
            - Ensure that comments maintain their original intent even when merged.
            - Consider the PR diff and comments closely while providing summary.

            ### Input Comments that needs to be summarized: 
            {self.params["COMMENTS"]}

            Below is a sample input structure for the comments you will receive:

            ### Sample Input containing two comments example:
            [
                {{
                "file_path": "app/services/cache.py",
                "line_number": 138,
                "line_hash":"75fdddd19961586137cae24da95e3514",
                "titles": [
                    "Hardcoded batch size (100) could lead to DoS",
                    "Fixed batch size needs optimization"
                ]
                "comments": [
                    "Security: The batch size is hardcoded to 100, which could be exploited to cause a Denial of 
                    Service (DoS) by forcing the system to process large or inefficient batches without control.",
                    "Performance": The current implementation uses a fixed batch size, which may not be optimal under 
                    varying load conditions and can lead to inefficient resource utilization or potential bottlenecks."
                ],
                "buckets": [
                    {{"name": "SECURITY", "agent_id": 50}},
                    {{"name": "PERFORMANCE", "agent_id": 24]}}
                ],
                "tags": ["Suggestion", "Suggestion"]
                "corrective_code": [
                    "BATCH_SIZE = config.get('REDIS_BATCH_SIZE', 100)",
                    "batch_size = max(100, min(1000, total_embeddings // 10))"
                ],
                "model": "Claude_3.5_Sonnet",
                "agent": "SECURITY",
                "confidence_score": 0.95,
                "is_valid": true,
                 "rationales": [
                    "The batch size value is hardcoded",
                    "Batch size is 100 and is being used uneffeciently"
                ],
                }},
                {{
                "file_path": "example/class.py",
                "line_number": 42,
                "line_hash":"75fdddd19961586137bvc24da95e3514",
                "titles": [
                    "Dry principal violated",
                    "Maintenance challenges due to bad code structure",
                    "Need better error handling"
                ]
                "comments": [
                    "MAINTAINABILITY: Duplicated method violates DRY principle.....more descriptive",
                    "CODE_ROBUSTNESS: Code structure leads to maintenance challenges.....more descriptive",
                    "RUNTIME_ERROR: Unique error handling approach needed.....more descriptive"
                ],
                "buckets": [
                    {{"name": "MAINTAINABILITY", "agent_id": 31}},
                    {{"name": "CODE_ROBUSTNESS", "agent_id": 35]}},
                    {{"name": "RUNTIME_ERROR", "agent_id": 22]}}
                ],
                "tags": ["Suggestion", "Suggestion", "Bug"]
                "corrective_code": [
                    "# Refactor to remove duplication",
                    "# Improve error handling strategy",
                    "# Implement unique error handling"
                ],
                "model": "Claude_3.5_Sonet",
                "agent": "MAINTAINABILITY",
                "confidence_score": 0.95,
                "is_valid": true,
                "rationales": [
                    "Method ABC is also define in file on line_number: 40",
                    "Code structure leads to maintenance challenges",
                    "Only general Exception is being catched"
                ],
                }}
            ]

            ### Format of Output:
            Return only validated comments with the following structure:
            ```JSON
                'comments': [{{
                'file_path': '<path of the file on which comment is being made, same as provided in input>',
                'line_number' : <line on which comment is relevant. Return the exact value present in the input>,
                'line_hash': <line_hash of line on which comment is relevant. Return the exact value present in the input>,
                'title': '<A single summarized title>'
                'comment': '<A single summarized comment for all the comments. Make bucket wise bullets in summary>',
                'corrective_code': '<Intelligently union of combined Corrective code for all the comments provided as a string. Strictly merge and provide corrective code only if input comments has corrective_code present inside comment>',
                'confidence_score': '<confidence_score field value in input comment>;,
                'buckets': <This is list of buckets [{{"name": <Bucket Name in which the comment falls. Keep it same as given in input comment>, "agent_id": <Id of the agent the comment is given by, Keep it same as given in input comment>}}]>,
                'tag': <If blending comments with tag Bug or Suggestion, prioritize Bug if any are Bug.>
                'model': <model field value in input comment>,
                'agent': <agent field value in input comment>,
                'is_valid': <is_valid field value in input comment. It can be true, false or null. Return as it is as mentioned in input comment>,
                'rationale': <A short combined rationale of all the comments>
                }}]
            ```

            ### Expected output example of provided input comments
            ```JSON
            'comments': [
                {{
                    "file_path": "app/services/cache.py",
                    "line_number": 138,
                    "line_hash":"75fdddd19961586137cae24da95e3514",
                    "title": "Hardcoded Batch Size (100) Risks DoS and Needs Optimization"
                    "comment": "- **SECURITY**: Hardcoded batch size (100) poses potential DoS risk through memory exhaustion\\n- **PERFORMANCE**: Implement dynamic batch sizing for optimal Redis operations",
                    "buckets": [
                        {{"name": "SECURITY", "agent_id": 50}},
                        {{"name": "PERFORMANCE", "agent_id": 24]}}
                    ],
                    "tag": "Suggestion",
                    "corrective_code": "# Configure dynamic batch size with security limits\nMAX_BATCH_SIZE = config.get('REDIS_MAX_BATCH_SIZE', 1000)\nMIN_BATCH_SIZE = config.get('REDIS_MIN_BATCH_SIZE', 100)\n\nbatch_size = max(MIN_BATCH_SIZE, min(MAX_BATCH_SIZE, total_embeddings // 10))\n\nfor i in range(0, len(cache_keys), batch_size):\n    batch = cache_keys[i:i + batch_size]",
                    "is_valid": true,
                    "confidence_score": 0.95,
                    "model": "Claude_3.5_Sonet",
                    "confidence_score": 0.95,
                    "is_valid": true,
                    "rationale": "Hardcoded batch size (100) limits flexibility and causes inefficiency.",
                }},
                {{
                    "file_path": "example/class.py",
                    "line_number": 42,
                    "line_hash":"75fdddd19961586137bvc24da95e3514",
                    "comment": "- **MAINTAINABILITY**: Duplicated method violates DRY principle and introduces maintenance challenges\\n- **RUNTIME_ERROR**: Unique error handling approach needed",
                    "buckets": [
                        {{"name": "MAINTAINABILITY", "agent_id": 31}},
                        {{"name": "RUNTIME_ERROR", "agent_id": 22]}}
                    ]
                    "tag": "Bug",
                    "corrective_code": "Intelligently combine: # Refactor to remove duplication and standardize method implementation and Implement comprehensive error handling strategy",
                    "is_valid": true,
                    "confidence_score": 0.95,
                    "model": "Claude_3.5_Sonet",
                    "confidence_score": 0.95,
                    "is_valid": true,
                    "rationale": "Duplicate method, poor structure, and broad exception reduce maintainability.",
                }}
            ]
            ```

            PR Diff on which comments needs to be validated:
            {self.params["PR_DIFF"]}


            ### Additional Guardrails
            To further improve accuracy and make the LLM behave like a skilled reviewer:

            1. Validation Step:
            - Explicitly request a validation pass before blending to avoid premature filtering.

            2. Multi-comment Merging:
                - For lines with multiple comments, ensure that all important details are retained, particularly those marked under business validation or user story.
                - For business validation comment if it is part of multiple comments don't loose any point while summarizing it in bullet point.
                - If there are n number of comments in "comments" list. then there are n number of buckets and n number of corrective code in buckets and corrective_code list in the same serial order. 

            3. Corrective Code Handling:
                - When merging multiple corrective code suggestions, intelligently combine and take union of them so that the final corrective_code field contains a comprehensive fix for the line in question.

            4. No missing comments.
                - No comments should be missed during processing. If input list contains 5 comments then we should get corresponding 5 comments in output response, each containing a summary as mentioned above.

            5. Unique Buckets:
                - If multiple comments exist for the same bucket on same line, merge the comments and return only unique buckets for a line in the specified structure.  

            6. Make sure to return response in json_object format only.

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
