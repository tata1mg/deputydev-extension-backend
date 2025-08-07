import asyncio
import json
from typing import Dict, List, Tuple

from deputydev_core.utils.config_manager import ConfigManager

from app.backend_common.models.dto.message_thread_dto import (
    LLModels,
)
from app.backend_common.services.chunking.rerankers.handler.llm_based.prompts.dataclasses.main import PromptFeatures
from app.backend_common.services.chunking.rerankers.handler.llm_based.prompts.factory import PromptFeatureFactory
from app.backend_common.services.llm.handler import LLMHandler
from app.main.blueprints.one_dev.models.dto.agent_chats import (
    ActorType,
    AgentChatDTO,
    MessageType,
    TextMessageData,
    ToolUseMessageData,
)
from app.main.blueprints.one_dev.models.dto.query_summaries import QuerySummaryDTO
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.previous_chats.dataclasses.main import (
    PreviousChats,
    RerankerDecision,
)
from app.main.blueprints.one_dev.services.code_generation.iterative_handlers.previous_chats.reranking.main import (
    LLMBasedChatFiltration,
)
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import QuerySolverInput
from app.main.blueprints.one_dev.services.repository.agent_chats.repository import AgentChatsRepository
from app.main.blueprints.one_dev.services.repository.query_summaries.query_summary_dto import (
    QuerySummarysRepository,
)


class ChatHistoryHandler:
    def __init__(self, previous_chat_payload: QuerySolverInput, llm_model: LLModels) -> None:
        self.payload = previous_chat_payload
        self.previous_chats: List[PreviousChats] = []
        self.query_id_to_chats_and_summary_map: Dict[int, Tuple[List[AgentChatDTO], QuerySummaryDTO | None]] = {}
        self.current_model: LLModels = llm_model

    def _get_approx_chat_text(self, query_id: int) -> str:
        agent_chats, _summary = self.query_id_to_chats_and_summary_map[query_id]
        message_data_text: str = ""
        for message_thread in agent_chats:
            if isinstance(message_thread.message_data, TextMessageData) or isinstance(
                message_thread.message_data, ToolUseMessageData
            ):
                message_data_text += json.dumps(message_thread.message_data.model_dump(mode="json"))
        return message_data_text

    def _estimate_chats_character_count(self, chats: List[PreviousChats]) -> int:
        total_chars = 0
        for chat in chats:
            chat_content = self._get_approx_chat_text(chat.id)
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
            token_limit = ConfigManager.configs["LLM_MODELS"][self.current_model.value]["LIMITS"][
                "SAFE_HISTORY_TOKEN_LIMIT"
            ]
            complete_content: str = ""
            for chat in self.previous_chats:
                complete_content += self._get_approx_chat_text(chat.id)
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

    def _set_query_id_to_chats_and_summary_map(
        self, all_agent_chats: List[AgentChatDTO], all_query_summaries: List[QuerySummaryDTO]
    ) -> None:
        # firstly create query_id to summary map
        query_id_to_summary_map: Dict[int, QuerySummaryDTO] = {}
        for query_summary in all_query_summaries:
            query_id_to_summary_map[query_summary.query_id] = query_summary

        # create a map of query_id to agent chats with summaries
        for agent_chat in all_agent_chats:
            if agent_chat.actor == ActorType.USER and agent_chat.message_type == MessageType.TEXT:
                self.query_id_to_chats_and_summary_map[agent_chat.query_id] = (
                    [agent_chat],
                    query_id_to_summary_map.get(agent_chat.id),
                )
            else:
                self.query_id_to_chats_and_summary_map[agent_chat.query_id][0].append(agent_chat)

    async def get_relevant_previous_agent_chats_for_new_query(self) -> List[AgentChatDTO]:
        # Fetch both query summaries and message threads concurrently, to save time in DB calls
        all_session_query_summaries, all_agent_chats = await asyncio.gather(
            QuerySummarysRepository.get_all_session_query_summaries(session_id=self.payload.session_id),
            AgentChatsRepository.get_chats_by_session_id(session_id=self.payload.session_id),
        )

        # Sort and limit to latest 10 queries
        all_session_query_summaries.sort(key=lambda x: x.query_id, reverse=False)
        if len(all_session_query_summaries) > 10:
            all_session_query_summaries = all_session_query_summaries[-10:]

        # now create a map of query_id to agent chats and summaries
        self._set_query_id_to_chats_and_summary_map(all_agent_chats, all_session_query_summaries)

        for _query_id, (agent_chats, query_summary) in self.query_id_to_chats_and_summary_map.items():
            query_agent_chat = agent_chats[0]
            if not isinstance(query_agent_chat.message_data, TextMessageData):
                raise ValueError(
                    f"Expected query message data to be of type TextMessageData, got {type(query_agent_chat.message_data)}"
                )

            # Create a PreviousChats object for each query, to be used by reranking
            self.previous_chats.append(
                PreviousChats(
                    id=query_agent_chat.query_id,
                    query=query_agent_chat.message_data.text,
                    summary=query_summary.summary if query_summary else query_agent_chat.message_data.text[:1000],
                )
            )

        # sort the previous chats based on query_id
        self.previous_chats.sort(key=lambda x: x.id, reverse=False)

        # this will keep max 5 most relevant chats
        filtered_query_ids = await self.filter_chat_summaries()

        all_relevant_agent_chats: List[AgentChatDTO] = []
        for query_id in filtered_query_ids:
            agent_chats, query_summary = self.query_id_to_chats_and_summary_map.get(query_id, ([], None))
            if agent_chats:
                all_relevant_agent_chats.extend(agent_chats)

        return all_relevant_agent_chats

    async def get_relevant_previous_agent_chats_for_tool_response_submission(self) -> List[AgentChatDTO]:
        # tool responses to submit
        tool_response_ids = [tool_response.tool_use_id for tool_response in self.payload.batch_tool_responses or []]

        all_agent_chats = await AgentChatsRepository.get_chats_by_session_id(session_id=self.payload.session_id)

        # get the tool request from the last agent_chat
        if not isinstance(all_agent_chats[-1].message_data, ToolUseMessageData):
            raise ValueError(
                f"Expected last message data to be of type ToolUseMessageData, got {type(all_agent_chats[-1].message_data)}"
            )

        tool_use_ids_in_previous_chats: List[str] = []
        tool_use_chats = all_agent_chats[-len(tool_response_ids) :]
        for tool_use_chat in tool_use_chats:
            if not isinstance(tool_use_chat.message_data, ToolUseMessageData):
                raise ValueError(
                    f"Expected tool use message data to be of type ToolUseMessageData, got {type(tool_use_chat.message_data)}"
                )
            tool_use_ids_in_previous_chats.append(tool_use_chat.message_data.tool_use_id)

        if set(tool_response_ids) != set(tool_use_ids_in_previous_chats):
            raise ValueError("Tool response IDs do not match with the tool use IDs in the previous chats.")

        # Filter chats based on specific query IDs
        relevant_agent_chats = [
            chat for chat in all_agent_chats if chat.query_id in tool_use_chats[-1].previous_queries
        ]
        return relevant_agent_chats
