from typing import Any, Dict, List

from deputydev_core.llm_handler.dataclasses.main import (
    NonStreamingParsedLLMCallResponse,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels

from app.backend_common.services.llm.llm_service_manager import LLMServiceManager
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    UserQueryEnhancerInput,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.dataclasses.main import (
    PromptFeatures,
)

from .prompts.factory import PromptFeatureFactory


class UserQueryEnhancer:
    def _get_response_from_parsed_llm_response(self, parsed_llm_response: List[Dict[str, Any]]) -> Dict[str, Any]:
        enhanced_query = None

        for response in parsed_llm_response:
            if response.get("enhanced_prompt"):
                enhanced_query = response["enhanced_prompt"]
                break

        return {
            "enhanced_query": enhanced_query,
        }

    async def get_enhanced_user_query(self, payload: UserQueryEnhancerInput) -> Dict[str, Any]:
        llm_handler = LLMServiceManager().create_llm_handler(
            prompt_factory=PromptFeatureFactory,
            prompt_features=PromptFeatures,
        )

        if payload.user_query:
            llm_response = await llm_handler.start_llm_query(
                session_id=payload.session_id,
                prompt_feature=PromptFeatures.USER_QUERY_ENHANCER,
                llm_model=LLModels.CLAUDE_3_POINT_7_SONNET,
                prompt_vars={"query": payload.user_query},
                previous_responses=[],
                stream=False,
            )

            if not isinstance(llm_response, NonStreamingParsedLLMCallResponse):
                raise ValueError("LLM response is not of type NonStreamingParsedLLMCallResponse")

            response = self._get_response_from_parsed_llm_response(
                parsed_llm_response=llm_response.parsed_content,
            )

            response["session_id"] = payload.session_id

            return response

        raise ValueError("query must be provided")
