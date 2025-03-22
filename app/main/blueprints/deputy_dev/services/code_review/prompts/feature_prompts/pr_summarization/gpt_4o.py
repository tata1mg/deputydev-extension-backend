from typing import Any, AsyncIterator, Dict, List

from app.backend_common.models.dto.message_thread_dto import MessageData, TextBlockData
from app.backend_common.services.llm.dataclasses.main import (
    NonStreamingResponse,
    StreamingResponse,
    UserAndSystemMessages,
)
from app.backend_common.services.llm.prompts.llm_base_prompts.gpt_4o import (
    BaseGPT4OPrompt,
)
from app.backend_common.utils.formatting import format_code_blocks

from ...dataclasses.main import PromptFeatures


class GPT4OPRSummarizationPrompt(BaseGPT4OPrompt):
    prompt_type = PromptFeatures.PR_SUMMARIZATION.value

    def __init__(self, params: Dict[str, Any]):
        self.params = params

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = """
            Your name is DeputyDev, receiving a user's comment thread carefully examine the smart code review analysis. 
            If the comment involves inquiries about code improvements or other technical discussions, evaluate the 
            provided pull request (PR) diff and offer appropriate resolutions. Otherwise, respond directly to 
            the posed question without delving into the PR diff. 
            include all the corrective_code inside ``` CODE ``` markdown"
        """

        user_message = f"""
            What does the following PR do ?
            Pull Request Title
            {self.params['PULL_REQUEST_TITLE']}

            Pull Request Diff:
            {self.params['PR_DIFF_WITHOUT_LINE_NUMBER']}
        """

        return UserAndSystemMessages(user_message=user_message, system_message=system_message)

    @classmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[str]:
        llm_parsed_response = []
        for response_data in llm_response.content:
            if isinstance(response_data, TextBlockData):
                summary = format_code_blocks(response_data.content.text)
                if summary:
                    llm_parsed_response.append(summary)

        return llm_parsed_response

    @classmethod
    async def get_parsed_streaming_events(cls, llm_response: StreamingResponse) -> AsyncIterator[Any]:
        raise NotImplementedError("Streaming events not supported for this prompt")

    @classmethod
    def get_parsed_response_blocks(cls, response_block: List[MessageData]) -> List[Dict[str, Any]]:
        raise NotImplementedError("This method must be implemented in the child class")
