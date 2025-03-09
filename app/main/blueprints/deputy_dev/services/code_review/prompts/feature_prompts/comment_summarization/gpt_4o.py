from typing import Any, AsyncIterator, Dict, List

from app.backend_common.services.llm.dataclasses.main import NonStreamingResponse, StreamingResponse, UserAndSystemMessages
from app.backend_common.services.llm.prompts.llm_base_prompts.gpt_4o import (
    BaseGPT4OPrompt,
)

from ...dataclasses.main import PromptFeatures


class GPT4OCommentSummarizationPrompt(BaseGPT4OPrompt):
    prompt_type = PromptFeatures.COMMENT_SUMMARIZATION.value

    def __init__(self, params: Dict[str, Any]):
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

        
            ### Guidelines:
            - Combine related feedback intelligently while preserving important details.
            - Use information from all buckets and comments to create a summary that incorporates the relevant feedback from each perspective.
            - Prioritize feedback based on severity and impact
            - Ensure that comments maintain their original intent even when merged.
            - Consider the PR diff and comments closely while providing summary.
            
            ### Input Comments that needs to be summarized: 
            {self.params['COMMENTS']}
        
            Below is a sample input structure for the comments you will receive:
            
            ### Sample Input containing two comments example:
            [
                {{
                "file_path": "app/services/cache.py",
                "line_number": "+138",
                "comments": [
                    "Security: Hardcoded batch size (100) could lead to DoS",
                    "Performance: Fixed batch size needs optimization"
                ],
                "buckets": [
                    {"name": "SECURITY", "agent_id": "c62142f5-3992-476d-9131-bf85e1beffb7"},
                    {"name": "PERFORMANCE", "agent_id": "36b9b529-3ad4-4ddf-9a12-8537ea9765a8"]}
                ],
                "corrective_code": [
                    "BATCH_SIZE = config.get('REDIS_BATCH_SIZE', 100)",
                    "batch_size = max(100, min(1000, total_embeddings // 10))"
                ],
                "model": "Claude_3.5_Sonet",
                "agent": "SECURITY",
                "confidence_score": 0.95,
                "is_valid": true
                }},
                {{
                "file_path": "example/class.py",
                "line_number": "42",
                "comments": [
                    "MAINTAINABILITY: Duplicated method violates DRY principle",
                    "CODE_ROBUSTNESS: Code structure leads to maintenance challenges",
                    "RUNTIME_ERROR: Unique error handling approach needed"
                ],
                "buckets": [
                    {"name": "MAINTAINABILITY", "agent_id": "c62142f5-3992-476d-9131-bf85e1beffb7"},
                    {"name": "CODE_ROBUSTNESS", "agent_id": "36b9b529-3ad4-4ddf-9a12-8537ea9765a8"]},
                    {"name": "RUNTIME_ERROR", "agent_id": "5932a405-96cb-4508-bfd4-443397583f95"]}
                ],
                "corrective_code": [
                    "# Refactor to remove duplication",
                    "# Improve error handling strategy",
                    "# Implement unique error handling"
                ],
                "model": "Claude_3.5_Sonet",
                "agent": "MAINTAINABILITY",
                "confidence_score": 0.95,
                "is_valid": true
                }}
            ]
            
            ### Format of Output:
            Return only validated comments with the following structure:
            ```JSON
                comments: [{{
                'file_path': '<path of the file on which comment is being made, same as provided in input>',
                'line_number' : <line on which comment is relevant. Return the exact value present with label `+` or `-` as present in the input>,
                'comment': '<A single summarized comment for all the comments. Make bucket wise bullets in summary>',
                'corrective_code': '<Intelligently union of combined Corrective code for all the comments provided as a string.>',
                'confidence_score': '<confidence_score field value in input comment>;,
                'buckets': <This is list of buckets [{"name": <Bucket Name in which the comment falls. Keep it same as given in input comment>, "agent_id": <Id of the agent the comment is given by, Keep it same as given in input comment>}]>,
                'model': <model field value in input comment>,
                'agent': <agent field value in input comment>,
                'is_valid': <is_valid field value in input comment. It can be true, false or null. Return as it is as mentioned in input comment>
                }}]
                ```
                
            ### Expected output example of provided input comments
            ```JSON
            comments: [
                {{
                    "file_path": "app/services/cache.py",
                    "line_number": "+138",
                    "comment": "- **SECURITY**: Hardcoded batch size (100) poses potential DoS risk through memory exhaustion\\n- **PERFORMANCE**: Implement dynamic batch sizing for optimal Redis operations",
                    "buckets": [
                        {"name": "SECURITY", "agent_id": "c62142f5-3992-476d-9131-bf85e1beffb7"},
                        {"name": "PERFORMANCE", "agent_id": "36b9b529-3ad4-4ddf-9a12-8537ea9765a8"]}
                    ],
                    "corrective_code": "# Configure dynamic batch size with security limits\nMAX_BATCH_SIZE = config.get('REDIS_MAX_BATCH_SIZE', 1000)\nMIN_BATCH_SIZE = config.get('REDIS_MIN_BATCH_SIZE', 100)\n\nbatch_size = max(MIN_BATCH_SIZE, min(MAX_BATCH_SIZE, total_embeddings // 10))\n\nfor i in range(0, len(cache_keys), batch_size):\n    batch = cache_keys[i:i + batch_size]",
                    "is_valid": true,
                    "confidence_score": 0.95,
                    "model": "Claude_3.5_Sonet",
                    "confidence_score": 0.95,
                    "is_valid": true
                }},
                {{
                    "file_path": "example/class.py",
                    "line_number": "42",
                    "comment": "- **MAINTAINABILITY**: Duplicated method violates DRY principle and introduces maintenance challenges\\n- **RUNTIME_ERROR**: Unique error handling approach needed",
                    "buckets": [
                        {"name": "MAINTAINABILITY", "agent_id": "c62142f5-3992-476d-9131-bf85e1beffb7"},
                        {"name": "RUNTIME_ERROR", "agent_id": "5932a405-96cb-4508-bfd4-443397583f95"]}
                    ]
                    "corrective_code": "Intelligently combine: # Refactor to remove duplication and standardize method implementation and Implement comprehensive error handling strategy",
                    "is_valid": true,
                    "confidence_score": 0.95,
                    "model": "Claude_3.5_Sonet",
                    "confidence_score": 0.95,
                    "is_valid": true
                }}
            ]
            ```
            
            PR Diff on which comments needs to be validated:
            {self.params['PR_DIFF']}
        
        
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
        
        """

        return UserAndSystemMessages(user_message=user_message, system_message=system_message)


    @classmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[Any]:
        raise NotImplementedError("This method must be implemented in the child class")

    @classmethod
    async def get_parsed_streaming_events(cls, llm_response: StreamingResponse) -> AsyncIterator[Any]:
        raise NotImplementedError("Streaming events not supported for this prompt")
