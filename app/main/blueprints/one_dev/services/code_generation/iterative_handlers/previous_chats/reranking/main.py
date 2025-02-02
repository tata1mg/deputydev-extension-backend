from typing import List

from app.backend_common.services.llm.handler import LLMHandler
from app.common.constants.constants import LLModels, PromptFeatures
from app.common.services.prompt.factory import PromptFeatureFactory
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.previous_chats.dataclass.main import (
    PreviousChats,
)


class LLMBasedChatFiltration:
    @classmethod
    async def rerank(
        cls,
        chats: List[PreviousChats],
        query: str,
    ) -> List[int]:
        prompt = PromptFeatureFactory.get_prompt(
            prompt_feature=PromptFeatures.CHAT_RERANKING,
            model_name=LLModels.CLAUDE_3_POINT_5_SONNET,
            init_params={
                "query": query,
                "chats": chats,
            },
        )
        response = await LLMHandler(prompt=prompt).get_llm_response_data(previous_responses=[])
        if response:
            filtered_chat_ids = response.parsed_llm_data["chat_ids"]
        else:
            # could be more better handling
            # default case
            filtered_chat_ids = [chat.id for chat in chats]
        return filtered_chat_ids
