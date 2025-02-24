# flake8: noqa
import json
from string import Template

from deputydev_core.services.chunking.utils.snippet_renderer import render_snippet_array
from torpedo import CONFIG

from app.main.blueprints.deputy_dev.constants.constants import AgentTypes
from app.main.blueprints.deputy_dev.services.code_review.agent_services.agent_base import (
    AgentServiceBase,
)
from app.main.blueprints.deputy_dev.services.code_review.context.context_service import (
    ContextService,
)


class OpenAICommentValidationAgent(AgentServiceBase):
    def __init__(self, context_service: ContextService, is_reflection_enabled: bool = False):
        super().__init__(context_service, is_reflection_enabled, AgentTypes.COMMENT_VALIDATION.value)
        self.model = CONFIG.config["FEATURE_MODELS"]["COMMENT_VALIDATION"]

    @staticmethod
    def get_comments_validation_system_prompt():
        return """
        You are an expert code reviewer assisting in validating the relevance and accuracy of code review comments.
        Evaluate each comment against the provided PR diff and relevant code snippets to confirm that they address 
        the changes in a useful and contextually appropriate way.
        """

    @staticmethod
    def get_comments_validation_user_prompt():
        return """
        Validate each provided comment's relevance in relation to the code changes shown in the PR diff and relevant code snippets based on following guardrails. 
        and only retain comments that accurately reflect meaningful feedback on the PR code changes.
        
        Objective:
        - Examine each comment based on the PR diff and the surrounding context provided.
        - If a comment is **not relevant** mark it invalid. Only return comments that accurately highlight a valid concern in the context of the PR diff. Ensure that no relevant feedback is missed.
        - Consider the `bucket` information to ensure that the feedback aligns with the purpose of the agent (e.g., a `security` comment should only address potential security issues).
        - If a comment is made for a change which is already being catered in the PR diff, mark that comment as invalid.
        - If the `corrective_code` and the comment description provided in the comment is already implemented or closely resembles the existing code in the PR diff, mark the comment as invalid.
        
        ### Input Comments that needs to be validated: 
        ${COMMENTS}
        
        Below is a sample input structure for the comments you will receive:
        
        ### Sample Input:
        
        Comments to Validate:
        [
            {{
                "file_path": "src/app.py",
                "line_number": +42,
                "comment": "Consider refactoring this function to improve readability.",
                "confidence_score": 0.85,
                "corrective_code": "def my_function(...): pass",
                "buckets": [{"name": "CODE_MAINTAINABILITY", "agent_id": "c62142f5-3992-476d-9131-bf85e1beffb7"}],
            }},
            {{
                "file_path": "src/utils.py",
                "line_number": 27,
                "comment": "Replace '==' with 'is' for comparison.",
                "confidence_score": 0.92,
                "corrective_code": "if x is None: pass",
                "buckets": [{"name": "CODE_MAINTAINABILITY", "agent_id": "c62142f5-3992-476d-9131-bf85e1beffb7"}],
            }}
        ]
        
        ### Format of Output:
        Return only validated comments with the following structure:
        ```JSON
            comments: [{{
            'file_path': '<path of the file on which comment is being made, same as provided in input>',
            'line_number' : <line on which comment is relevant. get this value from `<>` block at each code start in input. Return the exact value present with label `+` or `-` as present in the input>,
            'comment': '<Same comment as provided in input comment>',
            'corrective_code': '<Corrective code for the comment suggested. Same as provide in input>',
            'is_valid': <boolean value telling whether the comment is actually relevant or not>,
            "buckets": <This is list of buckets [{"name": <Bucket Name in which the comment falls. Keep it same as given in input comment>, "agent_id": <Id of the agent the comment is given by, Keep it same as given in input comment>}]>,
            }}]
            ```
            
        ###Expected output example 
        ```JSON
        comments: [
            {{
                "file_path": "src/app.py",
                "line_number": +42,
                "comment": "Consider refactoring this function to improve readability.",
                "corrective_code": "def my_function(...): pass"
                "is_valid": true,
                "buckets": [{"name": "CODE_MAINTAINABILITY", "agent_id": "c62142f5-3992-476d-9131-bf85e1beffb7"}],
            }},
            {{
                "file_path": "src/utils.py",
                "line_number": 27,
                "comment": "Replace '==' with 'is' for comparison.",
                "is_valid": false,
                "buckets": [{"name": "CODE_MAINTAINABILITY", "agent_id": "c62142f5-3992-476d-9131-bf85e1beffb7"}],
            }}
        ]
        ```
        
        PR Diff on which comments needs to be validated:
        <pr_diff>${PR_DIFF}</pr_diff>
        
        Relevant Code Snippets used to get context of changes in PR diff:
        <relevant_chunks_in_repo>${RELEVANT_CHUNKS}</relevant_chunks_in_repo>
        
        ### Guardrails:
        - Do not remove relevant comments. 
        - NEVER mark a comment as invalid just because it seems minor or stylistic
        - PRESERVE all comments that point to real code issues, even if they're not critical
        - Instruct the LLM to be conservative in discarding comments. It should only remove comments when there's clear evidence of irrelevance based on the context(i.e PR diff, relevant code snippets and content of the comment).
        - Keep all the fields same of a comment as provided in input just add a new key: value pair in each comment. Key as is_valid and its value a boolean which identify the relevancy of comment.
        - Ask the LLM to use the `bucket` tags as an additional validation layer. A comment’s relevance can be double-checked by ensuring it aligns with its `bucket` context (e.g., if it’s tagged as `security`, ensure it specifically addresses security concerns).
        - Any appreciation comments should be marked as invalid
        - All comments should be made on PR diff. And if any comment is made for relevant_chunks_in_repo mark it as invalid.
        - In case the comment is related to user story or business validation. Always mark it a valid comment. 
         """

    async def get_system_n_user_prompt(self, comments):
        system_message = self.get_comments_validation_system_prompt()
        prompt = self.get_comments_validation_user_prompt()
        user_message = await self.format_user_prompt(prompt, comments)
        return {
            "system_message": system_message,
            "user_message": user_message,
            "structure_type": "json_object",
            "parse": False,
            "exceeds_tokens": self.has_exceeded_token_limit(system_message, user_message),
        }

    async def format_user_prompt(self, prompt, comments):
        pr_diff = await self.context_service.get_pr_diff(append_line_no_info=True)
        relevant_chunks = await self.context_service.agent_wise_relevant_chunks()
        relevant_chunks = self.agent_relevant_chunk(relevant_chunks)
        prompt = Template(prompt)
        prompt_variables = {"PR_DIFF": pr_diff, "RELEVANT_CHUNKS": relevant_chunks, "COMMENTS": json.dumps(comments)}
        return prompt.safe_substitute(prompt_variables)

    def agent_relevant_chunk(self, relevant_chunks):
        relevant_chunks_indexes = relevant_chunks["comment_validation_relevant_chunks_mapping"]
        chunks = [relevant_chunks["relevant_chunks"][index] for index in relevant_chunks_indexes]
        return render_snippet_array(chunks)

    async def get_with_reflection_system_prompt_pass1(self):
        pass

    async def get_with_reflection_system_prompt_pass2(self):
        pass

    async def get_with_reflection_user_prompt_pass1(self):
        pass

    async def get_with_reflection_user_prompt_pass2(self):
        pass

    async def get_agent_specific_tokens_data(self):
        pass
