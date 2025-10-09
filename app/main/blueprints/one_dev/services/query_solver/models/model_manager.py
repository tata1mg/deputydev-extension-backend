import asyncio
from typing import Optional

from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels
from deputydev_core.utils.config_manager import ConfigManager

from app.backend_common.models.dto.extension_sessions_dto import ExtensionSessionData
from app.backend_common.repository.extension_sessions.repository import ExtensionSessionsRepository
from app.main.blueprints.one_dev.models.dto.agent_chats import (
    ActorType,
    AgentChatCreateRequest,
    InfoMessageData,
)
from app.main.blueprints.one_dev.models.dto.agent_chats import MessageType as ChatMessageType
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    Reasoning,
    RetryReasons,
)
from app.main.blueprints.one_dev.services.repository.agent_chats.repository import AgentChatsRepository


class ModelManager:
    """Handle LLM model operations for QuerySolver."""

    def get_model_change_text(
        self, current_model: LLModels, new_model: LLModels, retry_reason: Optional[RetryReasons]
    ) -> str:
        """Return a human-readable explanation of why the LLM model was changed."""

        def get_model_display_name(model_name: str) -> str:
            """Get the display name for a model from the configuration."""
            chat_models = ConfigManager.configs.get("CODE_GEN_LLM_MODELS", [])
            for model in chat_models:
                if model.get("name") == model_name:
                    return model.get("display_name", model_name)
            return model_name

        current_display = get_model_display_name(current_model.value)
        new_display = get_model_display_name(new_model.value)

        if retry_reason == RetryReasons.TOOL_USE_FAILED:
            return f"LLM model changed from {current_display} to {new_display} due to tool use failure."
        elif retry_reason == RetryReasons.THROTTLED:
            return f"LLM model changed from {current_display} to {new_display} due to throttling."
        elif retry_reason == RetryReasons.TOKEN_LIMIT_EXCEEDED:
            return f"LLM model changed from {current_display} to {new_display} due to token limit exceeded."
        else:
            return f"LLM model changed from {current_display} to {new_display} by the user."

    async def set_required_model(
        self,
        llm_model: LLModels,
        session_id: int,
        query_id: str,
        agent_name: str,
        retry_reason: Optional[RetryReasons],
        user_team_id: int,
        session_type: str,
        reasoning: Optional[Reasoning],
    ) -> None:
        """
        Set the required model for the session.
        """
        current_session = await ExtensionSessionsRepository.get_by_id(session_id=session_id)

        if not current_session:
            current_session = await ExtensionSessionsRepository.create_extension_session(
                extension_session_data=ExtensionSessionData(
                    session_id=session_id,
                    user_team_id=user_team_id,
                    session_type=session_type,
                    current_model=llm_model,
                )
            )

        if current_session.current_model != llm_model:
            # TODO: remove after v15 Force upgrade
            if (
                llm_model == LLModels.OPENROUTER_GPT_4_POINT_1
                and current_session.current_model == LLModels.GPT_4_POINT_1
            ):
                await asyncio.gather(
                    ExtensionSessionsRepository.update_session_llm_model(session_id=session_id, llm_model=llm_model),
                )
                return  # no need to store a message in chat as the models are equivalent

            # update current model in session
            await asyncio.gather(
                ExtensionSessionsRepository.update_session_llm_model(session_id=session_id, llm_model=llm_model),
                AgentChatsRepository.create_chat(
                    chat_data=AgentChatCreateRequest(
                        session_id=session_id,
                        actor=ActorType.SYSTEM,
                        message_data=InfoMessageData(
                            info=self.get_model_change_text(
                                current_model=LLModels(current_session.current_model),
                                new_model=llm_model,
                                retry_reason=retry_reason,
                            )
                        ),
                        message_type=ChatMessageType.INFO,
                        metadata={
                            "llm_model": llm_model.value,
                            "agent_name": agent_name,
                            **({"reasoning": reasoning.value} if reasoning else {}),
                        },
                        query_id=query_id,
                        previous_queries=[],
                    )
                ),
            )
