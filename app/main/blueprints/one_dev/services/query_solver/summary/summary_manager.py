import asyncio
from typing import List, Optional, tuple

from deputydev_core.llm_handler.core.handler import LLMHandler
from deputydev_core.llm_handler.dataclasses.main import NonStreamingParsedLLMCallResponse
from deputydev_core.llm_handler.dataclasses.unified_conversation_turn import (
    AssistantConversationTurn,
    ToolConversationTurn,
    UnifiedConversationTurn,
    UnifiedTextConversationTurnContent,
    UnifiedToolRequestConversationTurnContent,
    UnifiedToolResponseConversationTurnContent,
    UserConversationTurn,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import (
    LLModels,
    MessageCallChainCategory,
)

from app.main.blueprints.one_dev.models.dto.agent_chats import (
    ActorType,
    AgentChatDTO,
    CodeBlockData,
    TextMessageData,
    ToolUseMessageData,
)
from app.main.blueprints.one_dev.models.dto.agent_chats import MessageType as ChatMessageType
from app.main.blueprints.one_dev.models.dto.query_summaries import QuerySummaryData
from app.main.blueprints.one_dev.services.query_solver.prompts.dataclasses.main import PromptFeatures
from app.main.blueprints.one_dev.services.query_solver.prompts.factory import PromptFeatureFactory
from app.main.blueprints.one_dev.services.repository.agent_chats.repository import AgentChatsRepository
from app.main.blueprints.one_dev.services.repository.query_summaries.query_summary_dto import (
    QuerySummarysRepository,
)


class SummaryManager:
    """Handle summary operations for QuerySolver."""

    async def get_conversation_turns_for_summary(
        self, agent_chats: List[AgentChatDTO]
    ) -> List[UnifiedConversationTurn]:
        """Convert agent chats to conversation turns for summary generation."""
        conv_turns_for_summarization: List[UnifiedConversationTurn] = []

        for chat in agent_chats:
            if chat.actor == ActorType.USER:
                conv_turns_for_summarization.append(
                    UserConversationTurn(
                        content=[
                            UnifiedTextConversationTurnContent(
                                text=chat.message_data.text if isinstance(chat.message_data, TextMessageData) else ""
                            )
                        ]
                    )
                )
            elif chat.actor == ActorType.ASSISTANT:
                if chat.message_type == ChatMessageType.TEXT and isinstance(chat.message_data, TextMessageData):
                    conv_turns_for_summarization.append(
                        AssistantConversationTurn(
                            content=[UnifiedTextConversationTurnContent(text=chat.message_data.text)]
                        )
                    )
                elif chat.message_type == ChatMessageType.CODE_BLOCK and isinstance(chat.message_data, CodeBlockData):
                    code_content = f"```{chat.message_data.language}\n{chat.message_data.code}\n```"
                    if chat.message_data.file_path:
                        code_content = f"File: {chat.message_data.file_path}\n" + code_content
                    conv_turns_for_summarization.append(
                        AssistantConversationTurn(content=[UnifiedTextConversationTurnContent(text=code_content)])
                    )
                elif chat.message_type == ChatMessageType.TOOL_USE and isinstance(
                    chat.message_data, ToolUseMessageData
                ):
                    conv_turns_for_summarization.append(
                        AssistantConversationTurn(
                            content=[
                                UnifiedToolRequestConversationTurnContent(
                                    tool_name=chat.message_data.tool_name,
                                    tool_input=chat.message_data.tool_input,
                                    tool_use_id=chat.message_data.tool_use_id,
                                )
                            ]
                        )
                    )
                    if chat.message_data.tool_response:
                        conv_turns_for_summarization.append(
                            ToolConversationTurn(
                                content=[
                                    UnifiedToolResponseConversationTurnContent(
                                        tool_name=chat.message_data.tool_name,
                                        tool_use_response=chat.message_data.tool_response,
                                        tool_use_id=chat.message_data.tool_use_id,
                                    )
                                ]
                            )
                        )
                    else:
                        conv_turns_for_summarization.append(
                            ToolConversationTurn(
                                content=[
                                    UnifiedToolResponseConversationTurnContent(
                                        tool_name=chat.message_data.tool_name,
                                        tool_use_response={"result": "NO RESULT"},
                                        tool_use_id=chat.message_data.tool_use_id,
                                    )
                                ]
                            )
                        )

        prompt_handler = PromptFeatureFactory.get_prompt(
            model_name=LLModels.GPT_4_POINT_1_NANO,
            feature=PromptFeatures.QUERY_SUMMARY_GENERATOR,
        )(params={})
        user_and_system_message = prompt_handler.get_prompt()
        conv_turns_for_summarization.append(
            UserConversationTurn(
                content=[UnifiedTextConversationTurnContent(text=user_and_system_message.user_message)]
            )
        )

        return conv_turns_for_summarization

    async def generate_query_summary(
        self,
        session_id: int,
        query_id: str,
        llm_handler: LLMHandler[PromptFeatures],
    ) -> tuple[Optional[str], bool]:  # Always return a tuple
        """Generate query summary using LLM."""
        all_messages = await AgentChatsRepository.get_chats_by_session_id(session_id=session_id)
        # filter messages to be from current query only
        filtered_agent_chats = [chat for chat in all_messages if chat.query_id == query_id]
        filtered_agent_chats.sort(key=lambda x: x.created_at)

        conv_turns = await self.get_conversation_turns_for_summary(filtered_agent_chats)

        # then generate a more detailed summary using LLM
        llm_response = await llm_handler.start_llm_query(
            prompt_feature=PromptFeatures.QUERY_SUMMARY_GENERATOR,
            llm_model=LLModels.GPT_4_POINT_1_NANO,
            prompt_vars={},
            tools=[],
            stream=False,
            session_id=session_id,
            call_chain_category=MessageCallChainCategory.SYSTEM_CHAIN,
            conversation_turns=conv_turns,
        )

        if not isinstance(llm_response, NonStreamingParsedLLMCallResponse):
            raise ValueError("Expected NonStreamingParsedLLMCallResponse")
        query_summary = llm_response.parsed_content[0].summary or ""
        query_status = (
            llm_response.parsed_content[0].success if hasattr(llm_response.parsed_content[0], "success") else True
        )

        _summary_updation_task = asyncio.create_task(self.update_query_summary(query_id, query_summary, session_id))
        return query_summary, query_status

    async def update_query_summary(self, query_id: str, summary: str, session_id: int) -> None:
        """Update or create query summary in the database."""
        existing_summary = await QuerySummarysRepository.get_query_summary(session_id=session_id, query_id=query_id)
        if existing_summary:
            new_updated_summary = existing_summary.summary + "\n" + summary
            await QuerySummarysRepository.update_query_summary(
                session_id=session_id, query_id=query_id, summary=new_updated_summary
            )
        else:
            await QuerySummarysRepository.create_query_summary(
                QuerySummaryData(
                    session_id=session_id,
                    query_id=query_id,
                    summary=summary,
                )
            )
