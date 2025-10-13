from typing import List, Optional

from deputydev_core.llm_handler.core.handler import LLMHandler
from deputydev_core.llm_handler.dataclasses.main import NonStreamingParsedLLMCallResponse
from deputydev_core.llm_handler.models.dto.message_thread_dto import (
    LLModels,
    MessageCallChainCategory,
    MessageThreadDTO,
    MessageType,
)
from deputydev_core.utils.app_logger import AppLogger

from app.backend_common.repository.extension_sessions.repository import ExtensionSessionsRepository
from app.backend_common.repository.message_threads.repository import MessageThreadsRepository
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import FocusItem
from app.main.blueprints.one_dev.services.query_solver.prompts.dataclasses.main import PromptFeatures


class SessionManager:
    """Handle session-related operations for QuerySolver."""

    async def generate_session_summary(
        self,
        session_id: int,
        query: str,
        focus_items: List[FocusItem],
        llm_handler: LLMHandler[PromptFeatures],
        user_team_id: int,
        session_type: str,
    ) -> str:
        """Generate session summary using LLM."""
        current_session = await ExtensionSessionsRepository.find_or_create(session_id, user_team_id, session_type)
        if current_session and current_session.summary:
            return current_session.summary

        # if no summary, first generate a summary by directly putting first 100 characters of the query.
        # this will be used as a placeholder until the LLM generates a more detailed summary.
        brief_query_preview = query[:100]
        await ExtensionSessionsRepository.update_session_summary(
            session_id=session_id, summary=f"{brief_query_preview}..."
        )

        # then generate a more detailed summary using LLM
        llm_response = await llm_handler.start_llm_query(
            prompt_feature=PromptFeatures.SESSION_SUMMARY_GENERATOR,
            llm_model=LLModels.GEMINI_2_POINT_5_FLASH,
            prompt_vars={"query": query, "focus_items": focus_items},
            previous_responses=[],
            tools=[],
            stream=False,
            session_id=session_id,
            call_chain_category=MessageCallChainCategory.SYSTEM_CHAIN,
        )

        if not isinstance(llm_response, NonStreamingParsedLLMCallResponse):
            raise ValueError("Expected NonStreamingParsedLLMCallResponse")

        generated_summary = llm_response.parsed_content[0].get("summary")
        await ExtensionSessionsRepository.update_session_summary(session_id=session_id, summary=generated_summary)
        return generated_summary

    async def get_last_query_message_for_session(self, session_id: int) -> Optional[MessageThreadDTO]:
        """
        Get the last query message for the session.
        """
        try:
            messages = await MessageThreadsRepository.get_message_threads_for_session(
                session_id, call_chain_category=MessageCallChainCategory.CLIENT_CHAIN
            )
            last_query_message = None
            for message in messages:
                if message.message_type == MessageType.QUERY and message.prompt_type in [
                    "CODE_QUERY_SOLVER",
                    "CODE_QUERY_SOLVER",
                ]:
                    last_query_message = message
            return last_query_message
        except Exception as ex:  # noqa: BLE001
            AppLogger.log_error(f"Error occurred while fetching last query message for session {session_id}: {ex}")
            return None
