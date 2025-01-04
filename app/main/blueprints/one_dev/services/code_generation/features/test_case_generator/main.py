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
from app.main.blueprints.one_dev.services.code_generation.features.test_case_generator.dataclasses.main import (
    TestCaseGenerationInput,
)
from app.main.blueprints.one_dev.services.repository.code_generation_job.main import (
    JobService,
)
from app.main.blueprints.one_dev.services.repository.session_chat.main import (
    SessionChatService,
)


class TestCaseGenerationHandler(BaseCodeGenFeature[TestCaseGenerationInput]):
    feature = CodeGenFeature.TEST_CASE_GENERATION

    @classmethod
    async def _feature_task(
        cls, payload: TestCaseGenerationInput, job_id: int, llm_meta: List[LLMMeta]
    ) -> Dict[str, Any]:

        init_params = {
            "query": payload.query,
            "relevant_chunks": payload.relevant_chunks,
        }
        if payload.custom_instructions:
            init_params["custom_instructions"] = payload.custom_instructions
        prompt = PromptFeatureFactory.get_prompt(
            prompt_feature=PromptFeatures.TEST_GENERATION,
            model_name=LLModels.CLAUDE_3_POINT_5_SONNET,
            init_params=init_params,
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
                prompt_type=PromptFeatures.TEST_GENERATION,
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
            "display_response": llm_response.parsed_llm_data["response"],
            "session_id": payload.session_id,
        }
