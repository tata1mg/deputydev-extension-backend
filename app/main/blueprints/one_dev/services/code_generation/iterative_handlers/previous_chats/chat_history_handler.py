import asyncio
from typing import Dict, List, Tuple, Union

from deputydev_core.utils.config_manager import ConfigManager

from app.backend_common.models.dto.message_thread_dto import (
    MessageCallChainCategory,
    MessageThreadDTO,
    MessageType,
    TextBlockData,
)
from app.backend_common.repository.message_threads.repository import (
    MessageThreadsRepository,
)
from app.main.blueprints.one_dev.models.dto.query_summaries import QuerySummaryDTO
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.previous_chats.dataclasses.main import (
    PreviousChatPayload,
    PreviousChats,
)
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.previous_chats.reranking.main import (
    LLMBasedChatFiltration,
)
from app.main.blueprints.one_dev.services.repository.query_summaries.query_summary_dto import (
    QuerySummarysRepository,
)


class ChatHistoryHandler:
    def __init__(self, previous_chat_payload: PreviousChatPayload) -> None:
        self.payload = previous_chat_payload
        self.previous_chats: List[PreviousChats] = []
        self.data_map: Dict[int, Tuple[MessageThreadDTO, List[MessageThreadDTO], QuerySummaryDTO]] = {}

    def _get_entire_chat_content(self, chat: PreviousChats) -> str:
        # Get responses for this chat
        responses = self._get_responses_data_for_previous_chats(chat.id)
        responses_text = "\n".join(responses) if responses else ""

        # Combine query, summary, and responses
        chat_content = f"Query: {chat.query}\nSummary: {chat.summary}\nResponses: {responses_text}"
        return chat_content

    def _estimate_chats_character_count(self, chats: List[PreviousChats]) -> int:
        total_chars = 0
        for chat in chats:
            chat_content = self._get_entire_chat_content(chat)
            total_chars += len(chat_content)
        return total_chars

    def _estimate_chats_token_count(self, chats: List[PreviousChats]) -> int:
        total_tokens = 0
        for chat in chats:
            total_tokens += self._get_chat_token_count_from_db(chat.id)

        return total_tokens

    def _should_use_reranker(self, chats: List[PreviousChats]) -> str:
        if not chats:
            return "SAFE TO HANDLE"

        # First check characters of entire chat
        total_chars = self._estimate_chats_character_count(chats)

        # Get character limits from config
        char_limit_high = ConfigManager.configs["RERANKER"]["CHARACTER_LIMIT_HIGH"]
        char_limit_safe = ConfigManager.configs["RERANKER"]["CHARACTER_LIMIT_SAFE"]

        # If above character limit, surely rerank
        if total_chars >= char_limit_high:
            return "UNSAFE TO HANDLE"

        # If below safe character limit, don't rerank
        if total_chars <= char_limit_safe:
            return "SAFE TO HANDLE"

        # If in between, count tokens of entire chat and then decide
        return "NEED TO CHECK TOKENS"

    async def filter_chat_summaries(self) -> List[int]:
        if not self.previous_chats:
            return []

        reranking_decision = self._should_use_reranker(self.previous_chats)

        if reranking_decision == "SAFE TO HANDLE":
            # Return all chat IDs without reranking
            return [chat.id for chat in self.previous_chats]

        elif reranking_decision == "UNSAFE TO HANDLE":
            # Use reranker to filter down to most relevant chats
            reranked_chat_ids = await LLMBasedChatFiltration.rerank(
                self.previous_chats, self.payload.query, self.payload.session_id
            )
            return reranked_chat_ids

        else:  # uncertain case
            # Get precise token count and make decision
            token_limit = ConfigManager.configs["RERANKER"]["TOKEN_LIMIT"]
            precise_token_count = self._estimate_chats_token_count(self.previous_chats)
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

    def _get_chat_token_count_from_db(self, query_id: int) -> int:
        """
        Get the total token count for a chat from the database using stored LLM usage data.

        Args:
            query_id: The query ID to get token count for

        Returns:
            int: Total token count (input + output) for the chat
        """
        if query_id not in self.data_map:
            return 0

        query_message_thread, non_query_message_threads, _query_summary = self.data_map[query_id]
        total_tokens = 0

        # Add tokens from the query message thread
        if query_message_thread.usage:
            total_tokens += query_message_thread.usage.input + query_message_thread.usage.output

        # Add tokens from all response message threads
        for message_thread in non_query_message_threads:
            if message_thread.usage:
                total_tokens += message_thread.usage.input + message_thread.usage.output

        return total_tokens

    def _get_responses_data_for_previous_chats(self, query_id: int) -> List[str]:
        _query_message_thread, non_query_message_threads, _query_summary = self.data_map[query_id]
        responses: List[str] = []
        for message_thread in non_query_message_threads:
            if (
                message_thread.message_data
                and message_thread.message_data[0]
                and isinstance(message_thread.message_data[0], TextBlockData)
            ):
                responses.append(message_thread.message_data[0].content.text)
        return responses

    async def get_relevant_previous_chats(self) -> Dict[str, List[Dict[str, Union[str, int, List[str]]]]]:
        all_session_query_summaries = await QuerySummarysRepository.get_all_session_query_summaries(
            session_id=self.payload.session_id
        )
        all_session_query_summaries.sort(key=lambda x: x.query_id, reverse=False)

        # consider only latest 10 queries
        if len(all_session_query_summaries) > 10:
            all_session_query_summaries = all_session_query_summaries[-10:]

        gathered_result = await asyncio.gather(
            *[
                QuerySummarysRepository.get_all_session_query_summaries(session_id=self.payload.session_id),
                MessageThreadsRepository.get_message_threads_for_session(
                    session_id=self.payload.session_id, call_chain_category=MessageCallChainCategory.CLIENT_CHAIN
                ),
            ]
        )

        all_session_query_summaries: List[QuerySummaryDTO] = gathered_result[0]  # type: ignore
        all_query_message_threads: List[MessageThreadDTO] = gathered_result[1]  # type: ignore

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
        if not filtered_query_ids:
            return {"chats": []}

        response: List[Dict[str, Union[str, int, List[str]]]] = []
        for chat in self.previous_chats:
            if chat.id in filtered_query_ids:
                response.append(
                    {
                        "id": chat.id,
                        "response": self._get_responses_data_for_previous_chats(chat.id),
                        "query": chat.query,
                    }
                )
        return {"chats": response}
