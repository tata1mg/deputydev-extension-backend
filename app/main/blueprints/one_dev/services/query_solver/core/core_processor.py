import asyncio
from typing import Any, AsyncIterator, Dict, Optional
from uuid import uuid4

from deputydev_core.llm_handler.dataclasses.main import (
    PromptCacheConfig,
    StreamingEventType,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels
from deputydev_core.utils.app_logger import AppLogger
from pydantic import BaseModel

from app.backend_common.services.llm.llm_service_manager import LLMServiceManager
from app.backend_common.utils.dataclasses.main import ClientData
from app.main.blueprints.one_dev.models.dto.agent_chats import (
    ActorType,
    AgentChatCreateRequest,
    TextMessageData,
)
from app.main.blueprints.one_dev.models.dto.agent_chats import MessageType as ChatMessageType
from app.main.blueprints.one_dev.services.query_solver.agent.agent_manager import AgentManager
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    LLMModel,
    QuerySolverInput,
    Reasoning,
)
from app.main.blueprints.one_dev.services.query_solver.events.event_manager import EventManager
from app.main.blueprints.one_dev.services.query_solver.models.model_manager import ModelManager
from app.main.blueprints.one_dev.services.query_solver.prompts.dataclasses.main import PromptFeatures
from app.main.blueprints.one_dev.services.query_solver.prompts.factory import PromptFeatureFactory
from app.main.blueprints.one_dev.services.query_solver.session.session_manager import SessionManager
from app.main.blueprints.one_dev.services.query_solver.stream_handler.stream_handler import StreamHandler
from app.main.blueprints.one_dev.services.query_solver.stream_processing.stream_processor import StreamProcessor
from app.main.blueprints.one_dev.services.query_solver.tools.tool_response_manager import ToolResponseManager
from app.main.blueprints.one_dev.services.repository.agent_chats.repository import AgentChatsRepository
from app.main.blueprints.one_dev.utils.cancellation_checker import CancellationChecker


class CoreProcessor:
    """Handle core query processing operations for QuerySolver."""

    def __init__(self) -> None:
        self.agent_manager = AgentManager()
        self.model_manager = ModelManager()
        self.session_manager = SessionManager()
        self.tool_response_manager = ToolResponseManager()
        self.stream_processor = StreamProcessor()
        self.event_manager = EventManager()

    async def solve_query(
        self,
        payload: QuerySolverInput,
        client_data: ClientData,
        save_to_redis: bool = False,
        task_checker: Optional[CancellationChecker] = None,
        query_id: Optional[str] = None,
    ) -> AsyncIterator[BaseModel]:
        """Main query solving logic."""
        llm_handler = LLMServiceManager().create_llm_handler(
            prompt_factory=PromptFeatureFactory,
            prompt_features=PromptFeatures,
            cache_config=PromptCacheConfig(conversation=True, tools=True, system_message=True),
        )

        reasoning = Reasoning(payload.reasoning) if payload.reasoning else None

        # TODO: remove after v15 Force upgrade
        if payload.llm_model and LLMModel(payload.llm_model.value) == LLMModel.GPT_4_POINT_1:
            payload.llm_model = LLMModel.OPENROUTER_GPT_4_POINT_1

        if payload.query:
            # Handle new query
            return await self._handle_new_query(
                payload, client_data, llm_handler, reasoning, save_to_redis, task_checker, query_id
            )
        elif payload.batch_tool_responses:
            # Handle tool responses
            return await self._handle_tool_responses(payload, client_data, llm_handler, reasoning, task_checker)
        else:
            raise ValueError("Invalid input")

    async def _handle_new_query(
        self,
        payload: QuerySolverInput,
        client_data: ClientData,
        llm_handler: Any,
        reasoning: Optional[Reasoning],
        save_to_redis: bool,
        task_checker: Optional[CancellationChecker],
        query_id: Optional[str] = None,
    ) -> AsyncIterator[BaseModel]:
        """Handle new query processing."""
        # Use provided query_id if available, otherwise generate a new one
        generated_query_id = query_id or uuid4().hex

        if not payload.llm_model:
            raise ValueError("LLM model is required for query solving.")

        session_chats = await AgentChatsRepository.get_chats_by_session_id(session_id=payload.session_id)
        session_chats.sort(key=lambda x: x.created_at)

        agent_instance = await self.agent_manager.get_query_solver_agent_instance(
            payload=payload, llm_handler=llm_handler, previous_agent_chats=session_chats
        )

        await self.model_manager.set_required_model(
            llm_model=LLModels(payload.llm_model.value),
            session_id=payload.session_id,
            query_id=generated_query_id,
            agent_name=agent_instance.agent_name,
            retry_reason=payload.retry_reason,
            user_team_id=payload.user_team_id,
            session_type=payload.session_type,
            reasoning=reasoning,
        )

        new_query_chat = await AgentChatsRepository.create_chat(
            chat_data=AgentChatCreateRequest(
                session_id=payload.session_id,
                actor=ActorType.USER,
                message_data=TextMessageData(
                    text=payload.query,
                    attachments=payload.attachments,
                    focus_items=payload.focus_items,
                    vscode_env=payload.vscode_env,
                    repositories=payload.repositories,
                ),
                message_type=ChatMessageType.TEXT,
                metadata={
                    "llm_model": LLModels(payload.llm_model.value).value,
                    "agent_name": agent_instance.agent_name,
                },
                query_id=generated_query_id,
                previous_queries=[],
            )
        )

        _summary_task = asyncio.create_task(
            self.session_manager.generate_session_summary(
                session_id=payload.session_id,
                query=payload.query,
                focus_items=payload.focus_items,
                llm_handler=llm_handler,
                user_team_id=payload.user_team_id,
                session_type=payload.session_type,
            )
        )

        prompt_vars_to_use: Dict[str, Any] = {
            "query": payload.query,
            "focus_items": payload.focus_items,
            "deputy_dev_rules": payload.deputy_dev_rules,
            "write_mode": payload.write_mode,
            "os_name": payload.os_name,
            "shell": payload.shell,
            "vscode_env": payload.vscode_env,
            "repositories": payload.repositories,
        }

        model_to_use = LLModels(payload.llm_model.value)
        llm_inputs, previous_queries = await agent_instance.get_llm_inputs_and_previous_queries(
            payload=payload, _client_data=client_data, llm_model=model_to_use, new_query_chat=new_query_chat
        )

        prompt_vars_to_use = {**prompt_vars_to_use, **llm_inputs.extra_prompt_vars}

        llm_response = await llm_handler.start_llm_query(
            prompt_feature=PromptFeatures(llm_inputs.prompt.prompt_type),
            llm_model=model_to_use,
            reasoning=reasoning,
            prompt_vars=prompt_vars_to_use,
            attachments=payload.attachments,
            conversation_turns=llm_inputs.messages,
            tools=llm_inputs.tools,
            stream=True,
            session_id=payload.session_id,
            save_to_redis=save_to_redis,
            checker=task_checker,
            parallel_tool_calls=True,
            prompt_handler_instance=llm_inputs.prompt(params=prompt_vars_to_use),
            metadata={
                "agent_name": agent_instance.agent_name,
                **({"reasoning": reasoning.value} if reasoning else {}),
            },
        )
        return await self.stream_processor.get_final_stream_iterator(
            llm_response,
            session_id=payload.session_id,
            llm_handler=llm_handler,
            query_id=generated_query_id,
            previous_queries=previous_queries,
            llm_model=model_to_use,
            agent_name=agent_instance.agent_name,
            reasoning=reasoning,
            summary_task=_summary_task,
        )

    async def _handle_tool_responses(
        self,
        payload: QuerySolverInput,
        client_data: ClientData,
        llm_handler: Any,
        reasoning: Optional[Reasoning],
        task_checker: Optional[CancellationChecker],
    ) -> AsyncIterator[BaseModel]:
        """Handle tool response processing."""
        inserted_tool_responses = await asyncio.gather(
            *[
                self.tool_response_manager.store_tool_response_in_chat_chain(
                    tool_resp, payload.session_id, payload.vscode_env, payload.focus_items
                )
                for tool_resp in payload.batch_tool_responses
            ]
        )

        prompt_vars: Dict[str, Any] = {
            "os_name": payload.os_name,
            "shell": payload.shell,
            "vscode_env": payload.vscode_env,
            "write_mode": payload.write_mode,
            "deputy_dev_rules": payload.deputy_dev_rules,
        }

        agent_instance = await self.agent_manager.get_query_solver_agent_instance(
            payload=payload, llm_handler=llm_handler, previous_agent_chats=inserted_tool_responses
        )
        llm_to_use = LLModels(inserted_tool_responses[0].metadata["llm_model"])
        reasoning_val = inserted_tool_responses[0].metadata.get("reasoning")
        reasoning = Reasoning(reasoning_val) if reasoning_val else None
        if payload.retry_reason is not None:
            llm_to_use = LLModels(payload.llm_model.value)
            reasoning = Reasoning(payload.reasoning) if payload.reasoning else None

        await self.model_manager.set_required_model(
            llm_model=llm_to_use,
            session_id=payload.session_id,
            query_id=inserted_tool_responses[0].query_id,
            agent_name=agent_instance.agent_name,
            retry_reason=payload.retry_reason,
            user_team_id=payload.user_team_id,
            session_type=payload.session_type,
            reasoning=reasoning,
        )

        llm_inputs, previous_queries = await agent_instance.get_llm_inputs_and_previous_queries(
            payload=payload,
            _client_data=client_data,
            llm_model=llm_to_use,
        )
        prompt_vars_to_use = {**prompt_vars, **llm_inputs.extra_prompt_vars}
        llm_response = await llm_handler.start_llm_query(
            session_id=payload.session_id,
            tools=llm_inputs.tools,
            stream=True,
            prompt_vars=prompt_vars_to_use,
            checker=task_checker,
            parallel_tool_calls=True,
            prompt_feature=PromptFeatures(llm_inputs.prompt.prompt_type),
            llm_model=llm_to_use,
            reasoning=reasoning,
            conversation_turns=llm_inputs.messages,
        )

        return await self.stream_processor.get_final_stream_iterator(
            llm_response,
            session_id=payload.session_id,
            llm_handler=llm_handler,
            query_id=inserted_tool_responses[0].query_id,
            previous_queries=previous_queries,
            llm_model=llm_to_use,
            agent_name=agent_instance.agent_name,
            reasoning=reasoning,
        )

    async def solve_query_with_streaming(
        self,
        payload: QuerySolverInput,
        client_data: ClientData,
        query_id: str,
        task_checker: Optional[CancellationChecker] = None,
    ) -> None:
        """
        Internal method that handles the actual query solving with error handling
        and streams results to Redis.
        """
        from deputydev_core.exceptions.exceptions import InputTokenLimitExceededError
        from deputydev_core.exceptions.llm_exceptions import LLMThrottledError

        try:
            # Push stream initialization event first
            init_event = self.event_manager.create_stream_start_event()
            await asyncio.sleep(5)  # Small delay to ensure order
            await StreamHandler.push_to_stream(stream_id=query_id, data=init_event)

            # Get the stream iterator from the existing solve_query method
            stream_iterator = await self.solve_query(
                payload=payload,
                client_data=client_data,
                save_to_redis=True,
                task_checker=task_checker,
                query_id=query_id,
            )

            # Stream all events to Redis using StreamHandler
            last_event = None
            async for event in stream_iterator:
                last_event = event
                await StreamHandler.push_to_stream(stream_id=query_id, data=event)

            # Push completion events
            if (
                last_event
                and hasattr(last_event, "type")
                and last_event.type != StreamingEventType.TOOL_USE_REQUEST_END
            ):
                completion_event = self.event_manager.create_completion_event()
                await StreamHandler.push_to_stream(stream_id=query_id, data=completion_event)

                close_event = self.event_manager.create_close_event()
                await StreamHandler.push_to_stream(stream_id=query_id, data=close_event)
            else:
                end_event = self.event_manager.create_end_event()
                await StreamHandler.push_to_stream(stream_id=query_id, data=end_event)

        except LLMThrottledError as ex:
            AppLogger.log_error(f"LLM throttled error in query solver: {ex}")
            error_event = self.event_manager.create_llm_throttled_error_event(ex)
            await StreamHandler.push_to_stream(stream_id=query_id, data=error_event)

        except InputTokenLimitExceededError as ex:
            AppLogger.log_error(
                f"Input token limit exceeded: model={ex.model_name}, tokens={ex.current_tokens}/{ex.max_tokens}"
            )
            error_event = await self.event_manager.create_token_limit_error_event(ex, payload.query)
            await StreamHandler.push_to_stream(stream_id=query_id, data=error_event)

        except asyncio.CancelledError as ex:
            AppLogger.log_error(f"Query cancelled: {ex}")
            error_event = self.event_manager.create_error_event(f"LLM processing error: {str(ex)}")
            await StreamHandler.push_to_stream(stream_id=query_id, data=error_event)

        except Exception as e:  # noqa: BLE001
            # Handle other errors by pushing error event to stream
            AppLogger.log_error(f"Error in query solver: {e}")
            error_event = self.event_manager.create_error_event(f"LLM processing error: {str(e)}")
            await StreamHandler.push_to_stream(stream_id=query_id, data=error_event)
