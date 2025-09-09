from typing import List

from app.backend_common.services.llm.llm_service_manager import LLMServiceManager
from app.main.blueprints.one_dev.services.query_solver.agents.chat_history_handler.dataclasses.main import PreviousChats
from deputydev_core.llm_handler.dataclasses.main import (
    NonStreamingParsedLLMCallResponse,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import (
    LLModels,
    MessageCallChainCategory,
)

from ....prompts.dataclasses.main import PromptFeatures
from ....prompts.factory import PromptFeatureFactory


class LLMBasedChatFiltration:
    @classmethod
    async def rerank(
        cls,
        chats: List[PreviousChats],
        query: str,
        session_id: int,
    ) -> List[int]:
        llm_handler = LLMServiceManager().create_llm_handler(
            prompt_factory=PromptFeatureFactory,
            prompt_features=PromptFeatures,
        )

        llm_response = await llm_handler.start_llm_query(
            session_id=session_id,
            prompt_feature=PromptFeatures.CHAT_RERANKING,
            llm_model=LLModels.GPT_4_POINT_1_MINI,
            prompt_vars={
                "query": query,
                "chats": chats,
            },
            call_chain_category=MessageCallChainCategory.SYSTEM_CHAIN,
        )

        if not isinstance(llm_response, NonStreamingParsedLLMCallResponse):
            raise ValueError("LLM response is not of type NonStreamingParsedLLMCallResponse")

        filtered_chat_ids: List[int] = (
            llm_response.parsed_content[0]["chat_ids"]
            if llm_response.parsed_content and llm_response.parsed_content[0].get("chat_ids")
            else [chat.id for chat in chats]
        )
        return filtered_chat_ids
