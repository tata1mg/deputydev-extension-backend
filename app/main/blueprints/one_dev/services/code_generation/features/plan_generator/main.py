from typing import Any, Dict, List

from deputydev_core.services.chunking.utils.snippet_renderer import render_snippet_array

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.dataclasses.main import (
    LLMMeta,
    NonStreamingParsedLLMCallResponse,
)
from app.backend_common.services.llm.handler import LLMHandler
from app.main.blueprints.one_dev.services.code_generation.features.base_code_gen_feature import (
    BaseCodeGenFeature,
)
from app.main.blueprints.one_dev.services.code_generation.features.dataclass.main import (
    CodeGenFeature,
)
from app.main.blueprints.one_dev.services.code_generation.features.plan_generator.dataclasses.main import (
    CodePlanGenerationInput,
)
from app.main.blueprints.one_dev.services.code_generation.utils.utils import (
    get_response_code_lines,
)

from ...prompts.dataclasses.main import PromptFeatures
from ...prompts.factory import PromptFeatureFactory


class CodePlanHandler(BaseCodeGenFeature[CodePlanGenerationInput]):
    feature = CodeGenFeature.PLAN_GENERATION

    @classmethod
    async def _feature_task(
        cls, payload: CodePlanGenerationInput, job_id: int, llm_meta: List[LLMMeta]
    ) -> Dict[str, Any]:
        relevant_chunks = await cls.rerank(
            payload.query,
            payload.relevant_chunks,
            payload.focus_chunks or [],
            bool(payload.is_llm_reranking_enabled),
            sesison_id=payload.session_id,
        )
        relevant_chunks = render_snippet_array(relevant_chunks)

        llm_handler = LLMHandler(prompt_factory=PromptFeatureFactory, prompt_features=PromptFeatures)

        llm_response = await llm_handler.start_llm_query(
            session_id=payload.session_id,
            prompt_feature=PromptFeatures.TASK_PLANNER,
            llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
            prompt_vars={"query": payload.query, "relevant_chunks": relevant_chunks},
        )

        if not isinstance(llm_response, NonStreamingParsedLLMCallResponse):
            raise ValueError("LLM response is not of type NonStreamingParsedLLMCallResponse")

        # TODO: Move this to a separate function
        _code_lines = get_response_code_lines(llm_response.parsed_content[0]["response"])

        return {
            "session_id": payload.session_id,
            "display_response": llm_response.parsed_content[0]["response"],
        }
