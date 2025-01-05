from typing import Any, Dict, List

from app.backend_common.services.llm.handler import LLMHandler
from app.backend_common.services.llm.providers.dataclass.main import LLMMeta
from app.common.constants.constants import LLModels, PromptFeatures
from app.common.services.prompt.factory import PromptFeatureFactory
from app.main.blueprints.one_dev.models.dto.session_chat import SessionChatDTO
from app.main.blueprints.one_dev.services.code_generation.features.base_code_gen_feature import (
    BaseCodeGenFeature,
)
from app.main.blueprints.one_dev.services.code_generation.features.dataclass.main import (
    CodeGenFeature,
)
from app.main.blueprints.one_dev.services.code_generation.features.plan_generator.dataclasses.main import (
    CodePlanGenerationInput,
)
from app.main.blueprints.one_dev.services.repository.code_generation_job.main import (
    JobService,
)
from app.main.blueprints.one_dev.services.repository.session_chat.main import (
    SessionChatService,
)


class CodePlanHandler(BaseCodeGenFeature[CodePlanGenerationInput]):
    feature = CodeGenFeature.PLAN_GENERATION

    @classmethod
    async def _feature_task(
        cls, payload: CodePlanGenerationInput, job_id: int, llm_meta: List[LLMMeta]
    ) -> Dict[str, Any]:
        prompt = PromptFeatureFactory.get_prompt(
            prompt_feature=PromptFeatures.TASK_PLANNER,
            model_name=LLModels.CLAUDE_3_POINT_5_SONNET,
            init_params={"query": payload.query, "relevant_chunks": payload.relevant_chunks},
        )

        await JobService.db_update(
            filters={"id": job_id},
            update_data={"status": "PROMPT_GENERATED"},
        )

        llm_response = await LLMHandler(prompt=prompt).get_llm_response_data(previous_responses=[])
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
                prompt_type=PromptFeatures.TASK_PLANNER,
                llm_prompt=llm_response.raw_prompt,
                llm_response=llm_response.raw_llm_response,
                llm_model=LLModels.CLAUDE_3_POINT_5_SONNET.value,
            )
        )

        await JobService.db_update(
            filters={"id": job_id},
            update_data={"status": "LLM_RESPONSE"},
        )

        return {
            "session_id": payload.session_id,
            "display_response": llm_response.parsed_llm_data["response"],
        }
