import asyncio
from typing import Any, Dict, Optional

from app.backend_common.services.llm.llm_service_manager import LLMServiceManager
from deputydev_core.llm_handler.dataclasses.main import (
    NonStreamingParsedLLMCallResponse,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import (
    LLModels,
    MessageCallChainCategory,
)
from deputydev_core.utils.app_logger import AppLogger

from .prompts.dataclasses.main import PromptFeatures
from .prompts.factory import PromptFeatureFactory


class ReviewPlanner:
    def __init__(self, session_id: int, prompt_vars: Dict[str, Any]) -> None:
        super().__init__()
        self.session_id = session_id
        self.prompt_vars = prompt_vars
        self.llm_service_manager = LLMServiceManager()

    async def get_review_plan(self) -> Optional[Dict[str, Any]]:
        llm_handler = self.llm_service_manager.create_llm_handler(
            prompt_factory=PromptFeatureFactory,
            prompt_features=PromptFeatures,
        )

        max_retries = 2
        response: Optional[Dict[str, Any]] = None
        for attempt in range(max_retries + 1):
            try:
                llm_response = await llm_handler.start_llm_query(
                    session_id=self.session_id,
                    prompt_feature=PromptFeatures.PR_REVIEW_PLANNER,
                    llm_model=LLModels.GPT_O3_MINI,
                    prompt_vars=self.prompt_vars,
                    call_chain_category=MessageCallChainCategory.SYSTEM_CHAIN,
                )
                if llm_response:
                    if not isinstance(llm_response, NonStreamingParsedLLMCallResponse):
                        raise ValueError("Expected NonStreamingParsedLLMCallResponse")
                    response = llm_response.parsed_content[0]
                    break
            except Exception as e:  # noqa: BLE001
                AppLogger.log_warn(f"Review Planner call Attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(1)  # Optional: add a delay before retrying

        return response
