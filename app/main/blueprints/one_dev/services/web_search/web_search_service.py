from typing import Any, Dict, Optional

from app.backend_common.models.dto.message_thread_dto import (
    LLModels,
    MessageCallChainCategory,
)
from app.backend_common.services.llm.dataclasses.main import (
    NonStreamingParsedLLMCallResponse,
)
from app.backend_common.services.llm.handler import LLMHandler
from app.main.blueprints.one_dev.services.web_search.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.one_dev.services.web_search.factory import PromptFeatureFactory
from deputydev_core.utils.app_logger import AppLogger


class WebSearchService:
    @classmethod
    async def web_search(cls, session_id: int, query: str) -> Dict[str, Any]:
        llm_handler = LLMHandler(prompt_features=PromptFeatures, prompt_factory=PromptFeatureFactory)
        response: Optional[NonStreamingParsedLLMCallResponse] = None
        try:
            llm_response = await llm_handler.start_llm_query(
                session_id=session_id,
                prompt_feature=PromptFeatures.WEB_SEARCH,
                llm_model=LLModels.GEMINI_2_POINT_0_FLASH,
                prompt_vars={"descriptive_query": query},
                call_chain_category=MessageCallChainCategory.SYSTEM_CHAIN,
                search_web=True,
            )
            if llm_response:
                if not isinstance(llm_response, NonStreamingParsedLLMCallResponse):
                    raise ValueError("Expected NonStreamingParsedLLMCallResponse")
                response = llm_response
        except Exception as e:
            AppLogger.log_warn(f"Web search call failed: {e}")

        if response:
            generated_explanation: Dict[str, Any] = response.parsed_content
            return generated_explanation
        return {}
