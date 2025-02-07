from typing import List

from app.backend_common.services.llm.handler import LLMHandler
from app.backend_common.services.llm.providers.dataclass.main import LLMMeta
from app.common.constants.constants import LLModels, PromptFeatures
from app.common.services.chunking.utils.snippet_renderer import render_snippet_array
from app.common.services.prompt.factory import PromptFeatureFactory
from app.main.blueprints.one_dev.models.dto.session_chat import SessionChatDTO
from app.main.blueprints.one_dev.services.code_generation.features.base_code_gen_feature import (
    BaseCodeGenFeature,
)
from app.main.blueprints.one_dev.services.code_generation.features.code_generator.dataclasses.main import (
    CodeGenerationInput,
)
from app.main.blueprints.one_dev.services.code_generation.features.dataclass.main import (
    CodeGenFeature,
)
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.diff_creation.dataclasses.main import (
    DiffCreationInput,
)
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.diff_creation.main import (
    DiffCreationHandler,
)
from app.main.blueprints.one_dev.services.repository.code_generation_job.main import (
    JobService,
)
from app.main.blueprints.one_dev.services.repository.session_chat.main import (
    SessionChatService,
)
from app.main.blueprints.one_dev.services.code_generation.utils.utils import get_response_code_lines


class CodeGenerationHandler(BaseCodeGenFeature[CodeGenerationInput]):
    feature = CodeGenFeature.CODE_GENERATION

    @classmethod
    async def _feature_task(cls, payload: CodeGenerationInput, job_id: int, llm_meta: List[LLMMeta]):
        relevant_chunks = await cls.rerank(
            payload.query, payload.relevant_chunks, payload.focus_chunks, payload.is_llm_reranking_enabled
        )
        relevant_chunks = render_snippet_array(relevant_chunks)
        prompt = PromptFeatureFactory.get_prompt(
            prompt_feature=PromptFeatures.CODE_GENERATION,
            model_name=LLModels.CLAUDE_3_POINT_5_SONNET,
            init_params={"query": payload.query, "relevant_chunks": relevant_chunks},
        )

        await JobService.db_update(
            filters={"id": job_id},
            update_data={"status": "PROMPT_GENERATED"},
        )

        llm_response = await LLMHandler(prompt=prompt).get_llm_response_data(previous_responses=[])
        code_lines = get_response_code_lines(llm_response.parsed_llm_data["response"])
        llm_meta.append(llm_response.llm_meta)
        await JobService.db_update(
            filters={"id": job_id},
            update_data={
                "status": "LLM_RESPONSE",
                "meta_info": {
                    "llm_meta": [meta.model_dump(mode="json") for meta in llm_meta],
                },
                "llm_model": llm_response.llm_meta.llm_model.value,
                "loc": code_lines,
            },
        )

        await SessionChatService.db_create(
            SessionChatDTO(
                session_id=payload.session_id,
                prompt_type=PromptFeatures.CODE_GENERATION,
                llm_prompt=llm_response.raw_prompt,
                llm_response=llm_response.raw_llm_response,
                llm_model=llm_response.llm_meta.llm_model.value,
                response_summary=llm_response.parsed_llm_data["summary"],
                user_query=payload.query,
            )
        )

        final_resp = {
            "display_response": llm_response.parsed_llm_data["response"],
            "session_id": payload.session_id,
        }

        if not (payload.pr_config or payload.apply_diff):
            return final_resp

        diff_gen_output = await DiffCreationHandler.generate_diff_for_current_job(
            payload=DiffCreationInput(
                session_id=payload.session_id,
                pr_config=payload.pr_config,
                auth_data=payload.auth_data,
            ),
            job_id=job_id,
            llm_meta=llm_meta,
        )
        final_resp.update(diff_gen_output)
        return final_resp
