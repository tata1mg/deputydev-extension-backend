from typing import Any, Dict, List

from prompts.dataclasses.main import PromptFeatures
from prompts.factory import PromptFeatureFactory

from app.backend_common.services.llm.dataclasses.main import LLMMeta, LLModels
from app.backend_common.services.llm.handler import LLMHandler
from app.main.blueprints.one_dev.models.dto.session_chat import SessionChatDTO
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
from app.main.blueprints.one_dev.services.repository.code_generation_job.main import (
    JobService,
)
from app.main.blueprints.one_dev.services.repository.session_chat.main import (
    SessionChatService,
)


class PlanCodeGenerationHandler(BaseCodeGenIterativeHandler[PlanCodeGenerationInput]):
    feature = CodeGenIterativeHandlers.CHAT

    @classmethod
    async def _feature_task(
        cls, payload: PlanCodeGenerationInput, job_id: int, llm_meta: List[LLMMeta]
    ) -> Dict[str, Any]:

        previous_responses = await cls._get_previous_responses(payload)

        prompt = PromptFeatureFactory.get_prompt(
            prompt_feature=PromptFeatures.PLAN_CODE_GENERATION,
            model_name=LLModels.CLAUDE_3_POINT_5_SONNET,
            init_params={},
        )

        await JobService.db_update(
            filters={"id": job_id},
            update_data={"status": "PROMPT_GENERATED"},
        )

        llm_response = await LLMHandler(prompt_handler=prompt).get_llm_response_data(
            previous_responses=previous_responses
        )
        code_lines = get_response_code_lines(llm_response.parsed_llm_data["response"])
        llm_meta.append(llm_response.llm_meta)
        await JobService.db_update(
            filters={"id": job_id},
            update_data={
                "status": "LLM_RESPONSE",
                "meta_info": {
                    "llm_meta": [meta.model_dump(mode="json") for meta in llm_meta],
                },
            },
        )
        await SessionChatService.db_create(
            SessionChatDTO(
                session_id=payload.session_id,
                prompt_type=PromptFeatures.PLAN_CODE_GENERATION,
                llm_prompt=llm_response.raw_prompt,
                llm_response=llm_response.raw_llm_response,
                llm_model=LLModels.CLAUDE_3_POINT_5_SONNET.value,
                response_summary=llm_response.parsed_llm_data["summary"],
                user_query="plan to code",
                code_lines_count=code_lines,
            )
        )

        return {
            "session_id": payload.session_id,
            "display_response": llm_response.parsed_llm_data["response"],
        }
