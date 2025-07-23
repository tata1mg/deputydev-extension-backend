import asyncio
import json
from typing import Dict, List, Tuple

from deputydev_core.utils.config_manager import ConfigManager

from app.backend_common.models.dto.message_thread_dto import (
    LLModels,
    MessageCallChainCategory,
    MessageThreadDTO,
    MessageType,
    TextBlockData,
)
from app.backend_common.repository.message_threads.repository import (
    MessageThreadsRepository,
)
from app.backend_common.services.chunking.rerankers.handler.llm_based.prompts.dataclasses.main import PromptFeatures
from app.backend_common.services.chunking.rerankers.handler.llm_based.prompts.factory import PromptFeatureFactory
from app.backend_common.services.llm.handler import LLMHandler
from app.main.blueprints.one_dev.models.dto.query_summaries import QuerySummaryDTO
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.previous_chats.dataclasses.main import (
    PreviousChatPayload,
    PreviousChats,
    RerankerDecision,
)
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.previous_chats.reranking.main import (
    LLMBasedChatFiltration,
)
from app.main.blueprints.one_dev.services.repository.query_summaries.query_summary_dto import (
    QuerySummarysRepository,
)


class ChatHistoryHandler:
    def __init__(self, previous_chat_payload: PreviousChatPayload, llm_model: LLModels) -> None:
        self.payload = previous_chat_payload
        self.previous_chats: List[PreviousChats] = []
        self.data_map: Dict[int, Tuple[MessageThreadDTO, List[MessageThreadDTO], QuerySummaryDTO]] = {}
        self.current_model: LLModels = llm_model

    def _get_entire_chat_content(self, chat: PreviousChats) -> str:
        # Get responses for this chat
        responses_approx_text = self._get_approx_responses_text(chat.id)

        query_approx_text = ""
        for query_id, (query_message_thread, _non_query_message_threads, _query_summary) in self.data_map.items():
            if query_id == chat.id:
                query_approx_text = json.dumps(query_message_thread.message_data[0].content.model_dump(mode="json"))

        # Combine query, summary, and responses
        chat_content_approx = responses_approx_text + query_approx_text
        return chat_content_approx

    def _estimate_chats_character_count(self, chats: List[PreviousChats]) -> int:
        total_chars = 0
        for chat in chats:
            chat_content = self._get_entire_chat_content(chat)
            total_chars += len(chat_content)
        return total_chars

    def _should_use_reranker(self, chats: List[PreviousChats]) -> RerankerDecision:
        if not chats:
            return RerankerDecision.SAFE_TO_HANDLE

        # First check characters of entire chat
        total_chars = self._estimate_chats_character_count(chats)

        # Get character limits from config
        char_limit_high = ConfigManager.configs["LLM_MODELS"][self.current_model.value]["LIMITS"][
            "UNSAFE_HISTORY_CHARACTER_LIMIT"
        ]
        char_limit_safe = ConfigManager.configs["LLM_MODELS"][self.current_model.value]["LIMITS"][
            "SAFE_HISTORY_CHARACTER_LIMIT"
        ]

        # If above character limit, surely rerank
        if total_chars >= char_limit_high:
            return RerankerDecision.UNSAFE_TO_HANDLE

        # If below safe character limit, don't rerank
        if total_chars <= char_limit_safe:
            return RerankerDecision.SAFE_TO_HANDLE

        # If in between, count tokens of entire chat and then decide
        return RerankerDecision.NEED_TO_CHECK_TOKENS

    # TODO: This is a temp workaround, need to make this better and handle via the specific prompt handlers
    async def filter_chat_summaries(self) -> List[int]:
        if not self.previous_chats:
            return []

        reranking_decision = self._should_use_reranker(self.previous_chats)

        if reranking_decision == RerankerDecision.SAFE_TO_HANDLE:
            # Return all chat IDs without reranking
            return [chat.id for chat in self.previous_chats]

        elif reranking_decision == RerankerDecision.UNSAFE_TO_HANDLE:
            # Use reranker to filter down to most relevant chats
            reranked_chat_ids = await LLMBasedChatFiltration.rerank(
                self.previous_chats, self.payload.query, self.payload.session_id
            )
            return reranked_chat_ids

        else:  # RerankerDecision.NEED_TO_CHECK_TOKENS case
            # Get precise token count and make decision
            token_limit = ConfigManager.configs["LLM_MODELS"][self.current_model]["LIMITS"]["SAFE_HISTORY_TOKEN_LIMIT"]
            complete_content: str = ""
            for chat in self.previous_chats:
                complete_content += self._get_entire_chat_content(chat)
            handler = LLMHandler(prompt_features=PromptFeatures, prompt_factory=PromptFeatureFactory)
            precise_token_count = await handler.get_token_count(complete_content, self.current_model)
            if precise_token_count <= token_limit:
                # We can fit all chats within the limit
                return [chat.id for chat in self.previous_chats]
            else:
                # We need to use reranker to reduce the context
                reranked_chat_ids = await LLMBasedChatFiltration.rerank(
                    self.previous_chats, self.payload.query, self.payload.session_id
                )
                return reranked_chat_ids

    def _set_data_map(
        self, all_message_threads: List[MessageThreadDTO], all_query_summaries: List[QuerySummaryDTO]
    ) -> None:
        # firstly create query_id to summary map
        query_id_to_summary_map: Dict[int, QuerySummaryDTO] = {}
        for query_summary in all_query_summaries:
            query_id_to_summary_map[query_summary.query_id] = query_summary

        # create a map of query_id to message
        non_query_message_threads: List[MessageThreadDTO] = []
        for message_thread in all_message_threads:
            if message_thread.message_type == MessageType.QUERY and query_id_to_summary_map.get(message_thread.id):
                self.data_map[message_thread.id] = (message_thread, [], query_id_to_summary_map[message_thread.id])
            else:
                non_query_message_threads.append(message_thread)

        # add non query message threads to the map
        for message_thread in non_query_message_threads:
            if message_thread.query_id and message_thread.query_id in self.data_map:
                self.data_map[message_thread.query_id][1].append(message_thread)
            else:
                continue

    def _get_approx_responses_text(self, query_id: int) -> str:
        _query_message_thread, non_query_message_threads, _query_summary = self.data_map[query_id]
        message_data_text: str = ""
        for message_thread in non_query_message_threads:
            if message_thread.message_data:
                message_data_text = json.dumps(
                    [message_data.model_dump(mode="json") for message_data in message_thread.message_data]
                )
        return message_data_text

    async def get_relevant_previous_chats(self) -> List[MessageThreadDTO]:
        # Fetch both query summaries and message threads concurrently
        all_session_query_summaries, all_query_message_threads = await asyncio.gather(
            QuerySummarysRepository.get_all_session_query_summaries(session_id=self.payload.session_id),
            MessageThreadsRepository.get_message_threads_for_session(
                session_id=self.payload.session_id, call_chain_category=MessageCallChainCategory.CLIENT_CHAIN
            ),
        )

        if not all_session_query_summaries:
            return []

        # Sort and limit to latest 10 queries
        all_session_query_summaries.sort(key=lambda x: x.query_id, reverse=False)
        if len(all_session_query_summaries) > 10:
            all_session_query_summaries = all_session_query_summaries[-10:]

        self._set_data_map(all_query_message_threads, all_session_query_summaries)

        for _query_id, (query_message_thread, _non_query_message_threads, query_summary) in self.data_map.items():
            if (
                query_message_thread.message_data
                and query_message_thread.message_data[0]
                and isinstance(query_message_thread.message_data[0], TextBlockData)
                and query_message_thread.message_data[0].content_vars
                and query_message_thread.message_data[0].content_vars.get("query")
            ):
                self.previous_chats.append(
                    PreviousChats(
                        id=query_summary.query_id,
                        query=query_message_thread.message_data[0].content_vars["query"],
                        summary=query_summary.summary,
                    )
                )

        # sort the previous chats based on query_id
        self.previous_chats.sort(key=lambda x: x.id, reverse=False)

        # this will keep max 5 most relevant chats
        filtered_query_ids = await self.filter_chat_summaries()

        all_query_message_threads.sort(key=lambda x: x.id, reverse=False)

        return [
            response
            for response in all_query_message_threads
            if response.query_id in filtered_query_ids or response.id in filtered_query_ids
        ]
