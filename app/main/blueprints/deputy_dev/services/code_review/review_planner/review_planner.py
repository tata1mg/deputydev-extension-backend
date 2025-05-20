import asyncio
import time
from typing import Optional

from deputydev_core.utils.app_logger import AppLogger

from app.backend_common.models.dto.message_thread_dto import (
    LLModels,
    MessageCallChainCategory,
)
from app.backend_common.services.llm.dataclasses.main import (
    NonStreamingParsedLLMCallResponse,
)
from app.backend_common.services.llm.handler import LLMHandler

from .prompts.dataclasses.main import PromptFeatures
from .prompts.factory import PromptFeatureFactory


class ReviewPlanner:
    def __init__(self, session_id: int, prompt_vars) -> None:
        super().__init__()
        self.session_id = session_id
        self.prompt_vars = prompt_vars

    async def get_review_plan(self):
        llm_handler = LLMHandler(prompt_features=PromptFeatures, prompt_factory=PromptFeatureFactory)

        max_retries = 2
        response: Optional[NonStreamingParsedLLMCallResponse] = None
        for attempt in range(max_retries + 1):
            try:
                llm_response = await llm_handler.start_llm_query(
                    session_id=self.session_id,
                    prompt_feature=PromptFeatures.PR_REVIEW_PLANNER,
                    llm_model=LLModels.CLAUDE_3_POINT_7_SONNET,
                    prompt_vars=self.prompt_vars,
                    call_chain_category=MessageCallChainCategory.SYSTEM_CHAIN,
                )
                if llm_response:
                    if not isinstance(llm_response, NonStreamingParsedLLMCallResponse):
                        raise ValueError("Expected NonStreamingParsedLLMCallResponse")
                    response = llm_response.parsed_content[0]
                    break
            except Exception as e:
                AppLogger.log_warn(f"LLM reranking call Attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(1)  # Optional: add a delay before retrying

        return response
