# flake8: noqa
import json

from torpedo import CONFIG

from app.main.blueprints.deputy_dev.constants.constants import AgentTypes
from app.main.blueprints.deputy_dev.services.code_review.agent_services.agent_base import (
    AgentServiceBase,
)
from app.main.blueprints.deputy_dev.services.code_review.context.context_service import (
    ContextService,
)


class OpenAICommentSummarizationAgent(AgentServiceBase):
    def __init__(self, context_service: ContextService, is_reflection_enabled: bool = False):
        super().__init__(context_service, is_reflection_enabled, AgentTypes.COMMENT_SUMMARIZATION.value)
        self.model = CONFIG.config["FEATURE_MODELS"]["COMMENT_SUMMARIZATION"]

    @staticmethod
    def get_comments_summarization_system_prompt():
        return """
        You are an expert code reviewer responsible for summarizing and consolidating multiple code review comments on the same line of code into clear, actionable feedback.
        """

    @staticmethod
    def get_comments_summarization_user_prompt():
        return """
        You are acting as an Comments Reviewer for a Pull Request (PR). You will be given with a list of comments that are made on single line in a file, your job is to validate, filter, and summarize the feedback comments provided by multiple specialized agents. Your task involves:

        ###Context:
        - You have access to the PR diff provided below. Carefully review this diff to understand the changes in the code.
        - You will be given a list of comments object. Where each comment object consists of list of comments that are made on that particular line in that file.
          Each of those multiple comment has a comment, a bucket assigned to it, and a corrective code snippet attached to it. 
        - Each comment is tagged with its relevant `bucket` (such as `security`, `code communication`, `algorithm efficiency`) to indicate the type of feedback. Use this metadata to understand the context of each comment.
        - Multiple comments might reference the same line of code, but they come from different agents focusing on various aspects of the code.
    
        Objective:
         **Blending**:
           - For each line in the code where multiple comments exist, merge them into a single, concise summary.
           - The final summary of all the comments should contains bullet points bucket wise that Bucket as initial start of bullet point followed by combined summary for that bucket.
    
        ### Guidelines:
        - Combine related feedback intelligently while preserving important details.
        - Use information from all buckets and comments to create a summary that incorporates the relevant feedback from each perspective.
        - Prioritize feedback based on severity and impact
        - Ensure that comments maintain their original intent even when merged.
        - Consider the PR diff and comments closely while providing summary.
        - If single line have multiple comments and those comments contains some part of corrective code. Then in the final summarized comment intenlligenlty create the union of corrective code block for all comments with all the suggested fixes.
        
        ### Input Comments that needs to be summarized: 
        {comments}
    
        Below is a sample input structure for the comments you will receive:
        
        ### Sample Input:
        [
            {{
            "file_path": "app/services/cache.py",
            "line_number": "+138",
            "comments": [
                "Security: Hardcoded batch size (100) could lead to DoS",
                "Performance: Fixed batch size needs optimization"
            ],
            "buckets": ["SECURITY", "PERFORMANCE"],
            "corrective_code": [
                "BATCH_SIZE = config.get('REDIS_BATCH_SIZE', 100)",
                "batch_size = max(100, min(1000, total_embeddings // 10))"
            ],
            "model": "Claude_3.5_Sonet",
            "agent": "SECURITY",
            "confidence_score": 0.95
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
            'buckets': <List of buckets as provided in input>,
            'model': <model field value in input comment>,
            'agent': <agent field value in input comment>,
            }}]
            ```
            
        ### Expected output example 
        ```JSON
        comments: [
            {{
                "file_path": "app/services/cache.py",
                "line_number": "+138",
                "comment": "- **SECURITY**: Hardcoded batch size (100) poses potential DoS risk through memory exhaustion\\n- **PERFORMANCE**: Implement dynamic batch sizing for optimal Redis operations",
                "buckets": ["SECURITY", "PERFORMANCE"],
                "corrective_code": "# Configure dynamic batch size with security limits\nMAX_BATCH_SIZE = config.get('REDIS_MAX_BATCH_SIZE', 1000)\nMIN_BATCH_SIZE = config.get('REDIS_MIN_BATCH_SIZE', 100)\n\nbatch_size = max(MIN_BATCH_SIZE, min(MAX_BATCH_SIZE, total_embeddings // 10))\n\nfor i in range(0, len(cache_keys), batch_size):\n    batch = cache_keys[i:i + batch_size]",
                "is_valid": true,
                "confidence_score": 0.95,
                "model": "Claude_3.5_Sonet",
                "agent": "SECURITY",
                "confidence_score": 0.95
            }}
        ]
        ```
        
        PR Diff on which comments needs to be validated:
        {pr_diff}
    
    
        ### Additional Guardrails
        To further improve accuracy and make the LLM behave like a skilled reviewer:
        
        1. Validation Step:
           - Explicitly request a validation pass before blending to avoid premature filtering.
        
        2. Multi-comment Merging:
            - For lines with multiple comments, ensure that all important details are retained, particularly those marked under business validation.
            - For business validation comment if it is part of multiple comments don't loose any point while summarizing it in bullet point.
            - If there are n number of comments in "comments" list. then there are n number of buckets and n number of corrective code in buckets and corrective_code list in the same serial order. 
        
        3. Corrective Code Handling:
            - When merging multiple corrective code suggestions, intelligently combine them so that the final corrective_code field contains a comprehensive fix for the line in question.
        
        4. No missing comments.
            - No comments should be missed during processing. If input list contains 5 comments then we should get corresponding 5 comments in output response, each containing a summary as mentioned above.  
    
        """

    async def get_system_n_user_prompt(self, comments):
        pr_diff = await self.context_service.get_pr_diff(append_line_no_info=True)
        system_message = self.get_comments_summarization_system_prompt()
        user_message = self.get_comments_summarization_user_prompt().format(
            pr_diff=pr_diff, comments=json.dumps(comments)
        )
        return {
            "system_message": system_message,
            "user_message": user_message,
            "structure_type": "json_object",
            "parse": False,
            "exceeds_tokens": self.has_exceeded_token_limit(system_message, user_message),
        }

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
