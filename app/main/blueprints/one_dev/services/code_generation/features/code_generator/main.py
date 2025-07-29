from typing import List

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.dataclasses.main import (
    LLMMeta,
    NonStreamingParsedLLMCallResponse,
)
from app.backend_common.services.llm.handler import LLMHandler
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
from deputydev_core.services.chunking.utils.snippet_renderer import render_snippet_array

from ...prompts.dataclasses.main import PromptFeatures
from ...prompts.factory import PromptFeatureFactory


class CodeGenerationHandler(BaseCodeGenFeature[CodeGenerationInput]):
    feature = CodeGenFeature.CODE_GENERATION

    @classmethod
    async def _feature_task(cls, payload: CodeGenerationInput, job_id: int, llm_meta: List[LLMMeta]):
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
            prompt_feature=PromptFeatures.CODE_GENERATION,
            llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
            prompt_vars={
                "query": payload.query,
                "relevant_chunks": relevant_chunks,
            },
        )

        if not isinstance(llm_response, NonStreamingParsedLLMCallResponse):
            raise ValueError("LLM response is not of type NonStreamingParsedLLMCallResponse")

        # TODO: Move this to a separate function

        final_resp = {
            "display_response": llm_response.parsed_content[0]["response"],
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
