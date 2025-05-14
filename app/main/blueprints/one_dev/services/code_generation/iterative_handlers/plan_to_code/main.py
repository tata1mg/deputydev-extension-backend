from typing import Any, Dict, List

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.dataclasses.main import (
    LLMMeta,
    NonStreamingParsedLLMCallResponse,
)
from app.backend_common.services.llm.handler import LLMHandler
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.base_code_gen_iterative_handler import (
    BaseCodeGenIterativeHandler,
)
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.dataclass.main import (
    CodeGenIterativeHandlers,
)
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.plan_to_code.dataclasses.main import (
    PlanCodeGenerationInput,
)
from app.main.blueprints.one_dev.services.code_generation.utils.utils import (
    get_response_code_lines,
)

from ...prompts.dataclasses.main import PromptFeatures
from ...prompts.factory import PromptFeatureFactory


class PlanCodeGenerationHandler(BaseCodeGenIterativeHandler[PlanCodeGenerationInput]):
    feature = CodeGenIterativeHandlers.CHAT

    @classmethod
    async def _feature_task(
        cls, payload: PlanCodeGenerationInput, job_id: int, llm_meta: List[LLMMeta]
    ) -> Dict[str, Any]:
        llm_handler = LLMHandler(prompt_factory=PromptFeatureFactory, prompt_features=PromptFeatures)

        previous_responses = await cls._get_previous_responses(payload)

        llm_response = llm_handler.start_llm_query(
            session_id=payload.session_id,
            prompt_feature=PromptFeatures.PLAN_CODE_GENERATION,
            llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
            prompt_vars={},
            previous_responses=previous_responses,
        )

        if not isinstance(llm_response, NonStreamingParsedLLMCallResponse):
            raise ValueError("LLM response is not of type NonStreamingParsedLLMCallResponse")

        # TODO: Move this to a separate function
        _code_lines = get_response_code_lines(llm_response.parsed_content[0]["response"])

        return {
            "session_id": payload.session_id,
            "display_response": llm_response.parsed_content[0]["response"],
        }
