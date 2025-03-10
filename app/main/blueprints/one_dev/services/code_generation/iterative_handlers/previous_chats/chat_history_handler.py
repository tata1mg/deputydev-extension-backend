from typing import List

from app.main.blueprints.one_dev.models.dto.session_chat import SessionChatDTO
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.previous_chats.dataclasses.main import (
    PreviousChatPayload,
    PreviousChats,
)
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.previous_chats.reranking.main import (
    LLMBasedChatFiltration,
)
from app.main.blueprints.one_dev.services.code_generation.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.one_dev.services.repository.session_chat.main import (
    SessionChatService,
)


class ChatHistoryHandler:
    def __init__(self, previous_chat_payload: PreviousChatPayload):
        self.payload = previous_chat_payload
        self.session_chats: List[SessionChatDTO] = []

    async def get_relevant_previous_chats(self):
        all_session_chats = await SessionChatService.db_get(
            filters={
                "session_id": self.payload.session_id,
                "prompt_type__in": [
                    prompt_feature.value
                    for prompt_feature in [
                        PromptFeatures.CODE_GENERATION,
                        PromptFeatures.DOCS_GENERATION,
                        PromptFeatures.TASK_PLANNER,
                        PromptFeatures.TEST_GENERATION,
                        PromptFeatures.ITERATIVE_CODE_CHAT,
                        PromptFeatures.PLAN_CODE_GENERATION,
                    ]
                ],
            }
        )
        self.session_chats = sorted(all_session_chats, key=lambda x: x.created_at)
        chat_summaries_ids = await self.get_chat_summaries()
        response: List[dict] = []
        for chat in self.session_chats:
            if chat.id in chat_summaries_ids:
                response.append({"id": chat.id, "response": chat.llm_response, "query": chat.user_query})
        return {"chats": response}

    async def get_chat_summaries(self) -> List[int]:
        summaries: List[PreviousChats] = [
            PreviousChats(id=chat.id, query=chat.user_query, summary=chat.response_summary)
            for chat in self.session_chats
        ]
        summaries_ids = await self.filter_chat_summaries(summaries)
        return summaries_ids

    async def filter_chat_summaries(self, chats: List[PreviousChats]) -> List[int]:
        reranked_chat_ids = await LLMBasedChatFiltration.rerank(chats, self.payload.query, self.payload.session_id)
        return reranked_chat_ids
