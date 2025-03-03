from typing import Any, Dict, List

from app.backend_common.constants.constants import LLModels
from app.backend_common.services.llm.handler import LLMHandler
from app.backend_common.services.llm.providers.dataclass.main import LLMMeta
from app.common.constants.constants import PromptFeatures
from app.common.services.prompt.factory import PromptFeatureFactory
from app.main.blueprints.one_dev.models.dto.session_chat import SessionChatDTO
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.base_code_gen_iterative_handler import (
    BaseCodeGenIterativeHandler,
)
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.dataclass.main import (
    CodeGenIterativeHandlers,
)
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.iterative_chat.dataclasses.main import (
    IterativeChatInput,
)
from app.main.blueprints.one_dev.services.repository.code_generation_job.main import (
    JobService,
)
from app.main.blueprints.one_dev.services.repository.session_chat.main import (
    SessionChatService,
)


class IterativeChatHandler(BaseCodeGenIterativeHandler[IterativeChatInput]):
    feature = CodeGenIterativeHandlers.CHAT

    @classmethod
    async def _get_previous_responses(cls, payload: IterativeChatInput) -> List[Dict[str, str]]:
        previous_responses: List[Dict[str, str]] = []
        if payload.relevant_chat_history:
            for chat in payload.relevant_chat_history:
                previous_responses.append({"role": "user", "content": chat["query"]})
                previous_responses.append({"role": "assistant", "content": chat["response"]})

        return previous_responses

    @classmethod
    async def _feature_task(cls, payload: IterativeChatInput, job_id: int, llm_meta: List[LLMMeta]) -> Dict[str, Any]:
        prompt = PromptFeatureFactory.get_prompt(
            prompt_feature=PromptFeatures.ITERATIVE_CODE_CHAT,
            model_name=LLModels.CLAUDE_3_POINT_5_SONNET,
            init_params={"query": payload.query, "relevant_chunks": payload.relevant_chunks},
        )

        await JobService.db_update(
            filters={"id": job_id},
            update_data={"status": "PROMPT_GENERATED"},
        )
        previous_responses = await cls._get_previous_responses(payload)
        llm_response = await LLMHandler(prompt=prompt).get_llm_response_data(previous_responses=previous_responses)
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
                prompt_type=PromptFeatures.ITERATIVE_CODE_CHAT,
                llm_prompt=llm_response.raw_prompt,
                llm_response=llm_response.raw_llm_response,
                llm_model=LLModels.CLAUDE_3_POINT_5_SONNET.value,
                response_summary=llm_response.parsed_llm_data["summary"],
                user_query=payload.query,
            )
        )

        return {
            "session_id": payload.session_id,
            "display_response": llm_response.parsed_llm_data["response"],
        }
