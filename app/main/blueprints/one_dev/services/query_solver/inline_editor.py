from typing import Any, Dict

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.handler import LLMHandler
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    InlineEditInput,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.dataclasses.main import (
    PromptFeatures,
)

from .prompts.factory import PromptFeatureFactory


class InlineEditGenerator:
    async def get_inline_edit_diff_suggestion(self, payload: InlineEditInput) -> Dict[str, Any]:
        llm_handler = LLMHandler(prompt_factory=PromptFeatureFactory, prompt_features=PromptFeatures)
        llm_response = await llm_handler.start_llm_query(
            prompt_feature=PromptFeatures.INLINE_EDITOR,
            llm_model=LLModels.CLAUDE_3_POINT_5_SONNET,
            prompt_vars={
                "query": payload.query,
                "relevant_chunks": payload.relevant_chunks,
                "code_selection": payload.code_selection,
            },
            previous_responses=[],
            tools=[],
            stream=False,
            session_id=payload.session_id,
        )
        return llm_response.parsed_content[0]
