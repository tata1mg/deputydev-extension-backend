import json
from typing import Any, Dict, List, Optional, cast

from deputydev_core.llm_handler.core.handler import LLMHandler
from deputydev_core.llm_handler.dataclasses.main import (
    ConversationTool,
    NonStreamingParsedLLMCallResponse,
)
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
    ToolUseResponseContent,
    ToolUseResponseData,
)
from deputydev_core.llm_handler.prompts.base_prompt import BasePrompt
from deputydev_core.services.chunking.chunk_info import ChunkInfo
from deputydev_core.services.chunking.utils.snippet_renderer import render_snippet_array
from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.context_vars import get_context_value

from app.backend_common.utils.sanic_wrapper import CONFIG
from app.main.blueprints.deputy_dev.models.dto.review_agent_chats_dto import (
    ActorType,
    MessageType,
    ReviewAgentChatCreateRequest,
    ReviewAgentChatDTO,
    ReviewAgentChatUpdateRequest,
    TextMessageData,
    ToolUseMessageData,
)
from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import (
    AgentRunResult,
)
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.base_prompts.dataclasses.main import (
    LLMCommentData,
)
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.deputy_dev.services.code_review.common.tools.constants.tools_fallback import (
    EXCEPTION_RAISED_FALLBACK,
    NO_TOOL_USE_FALLBACK_PROMPT,
)
from app.main.blueprints.deputy_dev.services.code_review.common.tools.parse_final_response import PARSE_FINAL_RESPONSE
from app.main.blueprints.deputy_dev.services.code_review.common.tools.tool_request_manager import (
    ToolRequestManager,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.agents.base_code_review_agent import (
    BaseCodeReviewAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.vcs_review.context.context_service import (
    ContextService,
)
from app.main.blueprints.deputy_dev.services.repository.review_agent_chats.repository import ReviewAgentChatsRepository
from app.main.blueprints.deputy_dev.services.setting.setting_service import (
    SettingService,
)
from app.main.blueprints.deputy_dev.utils import repo_meta_info_prompt


class BaseCommenterAgent(BaseCodeReviewAgent):
    is_dual_pass: bool
    prompt_features: List[PromptFeatures]

    def __init__(
        self,
        context_service: ContextService,
        is_reflection_enabled: bool,
        llm_handler: LLMHandler[PromptFeatures],
        model: LLModels,
    ) -> None:
        super().__init__(context_service, is_reflection_enabled, llm_handler, model)
        self.agent_name = SettingService.helper.predefined_name_to_custom_name(self.agent_name)
        self.agent_setting = SettingService.helper.agent_setting_by_name(self.agent_name)
        self.agent_id = self.agent_setting.get("agent_id")
        self.display_name = self.agent_setting.get("display_name")
        self.tool_request_manager = ToolRequestManager(context_service=self.context_service)

    def agent_relevant_chunk(self, relevant_chunks: Dict[str, Any]) -> str:
        relevant_chunks_index = relevant_chunks["relevant_chunks_mapping"][self.agent_id]
        agent_relevant_chunks: List[ChunkInfo] = []
        for index in relevant_chunks_index:
            agent_relevant_chunks.append(relevant_chunks["relevant_chunks"][index])
        return render_snippet_array(agent_relevant_chunks)

    async def required_prompt_variables(self, last_pass_result: Optional[Any] = None) -> Dict[str, Optional[str]]:
        last_pass_comments_str = ""
        if last_pass_result:
            last_pass_comments: List[LLMCommentData] = last_pass_result.get("comments") or []
            last_pass_comments_str = json.dumps([comment.model_dump(mode="json") for comment in last_pass_comments])

        return {
            "PULL_REQUEST_TITLE": self.context_service.get_pr_title(),
            "PULL_REQUEST_DESCRIPTION": self.context_service.get_pr_description(),
            "PULL_REQUEST_DIFF": await self.context_service.get_pr_diff(
                append_line_no_info=True, agent_id=self.agent_id
            ),
            "REVIEW_COMMENTS_BY_JUNIOR_DEVELOPER": last_pass_comments_str,
            "USER_STORY": await self.context_service.get_user_story(),
            "PRODUCT_RESEARCH_DOCUMENT": await self.context_service.get_confluence_doc(),
            "PR_DIFF_WITHOUT_LINE_NUMBER": await self.context_service.get_pr_diff(agent_id=self.agent_id),
            "AGENT_OBJECTIVE": self.agent_setting.get("objective", ""),
            "CUSTOM_PROMPT": self.agent_setting.get("custom_prompt") or "",
            "BUCKET": self.agent_setting.get("display_name"),
            "REPO_INFO_PROMPT": repo_meta_info_prompt(get_context_value("setting").get("app", {})),
            "AGENT_NAME": self.agent_type.value,
        }

    def get_additional_info_prompt(self, tokens_info: Any, reflection_iteration: Any) -> Dict[str, Any]:
        return {
            "key": self.agent_name,
            "comment_confidence_score": self.agent_setting.get("confidence_score"),
            "model": self.model,
            "tokens": tokens_info,
            "reflection_iteration": reflection_iteration,
        }

    def get_display_name(self) -> str:
        return self.agent_setting.get("display_name")

    def _get_conversation_turns_from_chat(
        self, chat_dto_list: List[ReviewAgentChatDTO]
    ) -> List[UnifiedConversationTurn]:
        conversation_turns: List[UnifiedConversationTurn] = []
        for chat in chat_dto_list:
            if isinstance(chat.message_data, TextMessageData) and chat.actor == ActorType.REVIEW_AGENT:
                conversation_turns.append(
                    UserConversationTurn(
                        content=[UnifiedTextConversationTurnContent(text=chat.message_data.text)],
                        cache_breakpoint=chat.metadata.get("cache_breakpoint"),
                    )
                )
            elif isinstance(chat.message_data, ToolUseMessageData) and chat.actor == ActorType.ASSISTANT:
                conversation_turns.append(
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
                    conversation_turns.append(
                        ToolConversationTurn(
                            content=[
                                UnifiedToolResponseConversationTurnContent(
                                    tool_name=chat.message_data.tool_name,
                                    tool_use_response=chat.message_data.tool_response
                                    if isinstance(chat.message_data.tool_response, dict)
                                    else {"response": chat.message_data.tool_response},
                                    tool_use_id=chat.message_data.tool_use_id,
                                )
                            ]
                        )
                    )
        return conversation_turns

    async def run_agent(self, session_id: int) -> AgentRunResult:  # noqa: C901
        """
        Run the agent and return the agent run result
        """
        total_passes = 1 if not self.is_dual_pass else 2
        last_pass_result: Optional[Any] = None
        tokens_data: Dict[str, Dict[str, Any]] = {}

        for pass_num in range(1, total_passes + 1):
            prompt_feature = self.prompt_features[pass_num - 1]  # 0 indexed

            # check if the token limit has been exceeded
            prompt_vars = await self.required_prompt_variables(last_pass_result=last_pass_result or {})
            prompt_handler = self.llm_handler.prompt_handler_map.get_prompt(
                model_name=self.model, feature=prompt_feature
            )(prompt_vars)
            user_and_system_messages = prompt_handler.get_prompt()
            current_tokens_data = self.get_tokens_data(user_and_system_messages)
            token_limit_exceeded = self.has_exceeded_token_limit(user_and_system_messages)

            token_key = f"{self.agent_name}PASS_{pass_num}"
            tokens_data[token_key] = current_tokens_data

            if token_limit_exceeded:
                return AgentRunResult(
                    agent_result=None,
                    prompt_tokens_exceeded=True,
                    agent_name=self.agent_name,
                    agent_type=self.agent_type,
                    model=self.model,
                    tokens_data=tokens_data,
                )

            # Get the tools to use for PR review flow
            tools_to_use = self.get_tools_for_review(prompt_handler)

            chat_dto_list: List[ReviewAgentChatDTO] = []

            # store the review diff
            cached_chat = await ReviewAgentChatsRepository.create_chat(
                ReviewAgentChatCreateRequest(
                    session_id=session_id,
                    agent_id=str(self.agent_id),
                    actor=ActorType.REVIEW_AGENT,
                    message_type=MessageType.TEXT,
                    message_data=TextMessageData(text=user_and_system_messages.cached_message),
                    metadata={"cache_breakpoint": True},
                )
            )
            chat_dto_list.append(cached_chat)

            # store the first query in review_agent_chats
            start_chat = await ReviewAgentChatsRepository.create_chat(
                ReviewAgentChatCreateRequest(
                    session_id=session_id,
                    agent_id=str(self.agent_id),
                    actor=ActorType.REVIEW_AGENT,
                    message_type=MessageType.TEXT,
                    message_data=TextMessageData(text=user_and_system_messages.user_message),
                    metadata={},
                )
            )
            chat_dto_list.append(start_chat)

            # Initial query to the LLM
            llm_response = await self.llm_handler.start_llm_query(
                session_id=session_id,
                prompt_feature=prompt_feature,
                llm_model=self.model,
                prompt_vars=prompt_vars,
                tools=tools_to_use,
                conversation_turns=self._get_conversation_turns_from_chat(chat_dto_list),
            )

            if not isinstance(llm_response, NonStreamingParsedLLMCallResponse):
                raise ValueError(f"LLM Response is not of type NonStreamingParsedLLMCallResponse: {llm_response}")

            tokens_data[token_key].update(
                {
                    "input_tokens": llm_response.usage.input,
                    "output_tokens": llm_response.usage.output,
                }
            )

            # Process tool use requests iteratively
            current_response: NonStreamingParsedLLMCallResponse = llm_response
            max_iterations: int = cast(
                int,
                CONFIG.config[  # type: ignore
                    "MAX_REVIEW_TOOL_ITERATIONS"
                ],
            )  # Limit the number of iterations to prevent infinite loops
            iteration_count: int = 0

            while iteration_count <= max_iterations:
                # Check if parse_final_response tool is used
                if self.tool_request_manager.is_final_response(current_response):
                    try:
                        # extract final response tool use
                        tool_use_requests = self.tool_request_manager.get_tool_use_request_data(
                            current_response, session_id
                        )
                        if not tool_use_requests:
                            raise ValueError(f"No tool use request found in LLM response: {current_response}")
                        # store final response in review_agent_chats
                        current_turn_chat = await ReviewAgentChatsRepository.create_chat(
                            ReviewAgentChatCreateRequest(
                                session_id=session_id,
                                agent_id=str(self.agent_id),
                                actor=ActorType.ASSISTANT,
                                message_type=MessageType.TOOL_USE,
                                message_data=ToolUseMessageData(
                                    tool_name=tool_use_requests[0].content.tool_name,
                                    tool_input=tool_use_requests[0].content.tool_input,
                                    tool_use_id=tool_use_requests[0].content.tool_use_id,
                                ),
                                metadata={},
                            )
                        )
                        chat_dto_list.append(current_turn_chat)
                        final_response = self.tool_request_manager.extract_final_response(current_response)

                        last_pass_result = final_response
                        break
                    except Exception as e:  # noqa: BLE001
                        AppLogger.log_error(f"Error processing parse_final_response Retrying with LLM : {e}")
                        # Create a tool use response with error feedback
                        tool_use_responses = ToolUseResponseData(
                            content=ToolUseResponseContent(
                                tool_name="parse_final_response",
                                tool_use_id=current_response.parsed_content[0].content.tool_use_id,
                                response=EXCEPTION_RAISED_FALLBACK.format(
                                    tool_name="parse_final_response",
                                    tool_input=json.dumps(
                                        current_response.parsed_content[0].content.tool_input, indent=2
                                    ),
                                    error_message=str(e),
                                ),
                            )
                        )

                        # store the tool use response in the last tool_request chat in review_agent_chats
                        last_chat = chat_dto_list[-1]
                        if isinstance(last_chat.message_data, ToolUseMessageData):
                            last_chat.message_data.tool_response = (
                                tool_use_responses.content.response
                                if isinstance(tool_use_responses.content.response, dict)
                                else {"response": tool_use_responses.content.response}
                            )
                        await ReviewAgentChatsRepository.update_chat(
                            chat_id=last_chat.id,
                            update_data=ReviewAgentChatUpdateRequest(message_data=last_chat.message_data),
                        )

                        # Submit the error feedback to the LLM
                        current_turn_response = await self.llm_handler.start_llm_query(
                            session_id=session_id,
                            tools=tools_to_use,
                            conversation_turns=self._get_conversation_turns_from_chat(chat_dto_list),
                            prompt_feature=prompt_feature,
                            llm_model=self.model,
                            prompt_vars=prompt_vars,
                        )
                        if not isinstance(current_turn_response, NonStreamingParsedLLMCallResponse):
                            raise ValueError(
                                f"LLM Response is not of type NonStreamingParsedLLMCallResponse: {current_turn_response}"
                            )
                        current_response = current_turn_response
                        iteration_count += 1
                        continue

                if not hasattr(current_response, "parsed_content") or not current_response.parsed_content:
                    # No tool use request block received
                    # store feedback query in review_agent_chats

                    current_turn_chat = await ReviewAgentChatsRepository.create_chat(
                        ReviewAgentChatCreateRequest(
                            session_id=session_id,
                            agent_id=str(self.agent_id),
                            actor=ActorType.REVIEW_AGENT,
                            message_type=MessageType.TEXT,
                            message_data=TextMessageData(text=NO_TOOL_USE_FALLBACK_PROMPT),
                            metadata={},
                        )
                    )
                    chat_dto_list.append(current_turn_chat)
                    current_turn_response = await self.llm_handler.start_llm_query(
                        session_id=session_id,
                        tools=tools_to_use,
                        conversation_turns=self._get_conversation_turns_from_chat(chat_dto_list),
                        prompt_feature=prompt_feature,
                        llm_model=self.model,
                        prompt_vars=prompt_vars,
                    )
                    if not isinstance(current_turn_response, NonStreamingParsedLLMCallResponse):
                        raise ValueError(
                            f"LLM Response is not of type NonStreamingParsedLLMCallResponse: {current_turn_response}"
                        )
                    current_response = current_turn_response
                    iteration_count += 1

                else:
                    # Iterative tool use
                    tool_use_requests = self.tool_request_manager.get_tool_use_request_data(
                        current_response, session_id
                    )

                    if tool_use_requests:
                        for tool_use_request in tool_use_requests:
                            # store tool use request in review_agent_chats
                            current_turn_chat = await ReviewAgentChatsRepository.create_chat(
                                ReviewAgentChatCreateRequest(
                                    session_id=session_id,
                                    agent_id=str(self.agent_id),
                                    actor=ActorType.ASSISTANT,
                                    message_type=MessageType.TOOL_USE,
                                    message_data=ToolUseMessageData(
                                        tool_use_id=tool_use_request.content.tool_use_id,
                                        tool_input=tool_use_request.content.tool_input,
                                        tool_name=tool_use_request.content.tool_name,
                                    ),
                                    metadata={},
                                )
                            )

                            chat_dto_list.append(current_turn_chat)

                        tool_use_responses = await self.tool_request_manager.process_tool_use_request(
                            current_response, session_id
                        )

                        if tool_use_responses:
                            if iteration_count == max_iterations - 1:
                                prompt_vars["final_breach"] = "true"

                        for tool_response in tool_use_responses:
                            corresp_tool_request = next(
                                (
                                    req
                                    for req in chat_dto_list
                                    if isinstance(req.message_data, ToolUseMessageData)
                                    and req.message_data.tool_use_id == tool_response.content.tool_use_id
                                ),
                                None,
                            )
                            if corresp_tool_request and isinstance(
                                corresp_tool_request.message_data, ToolUseMessageData
                            ):
                                corresp_tool_request.message_data.tool_response = (
                                    tool_response.content.response
                                    if isinstance(tool_response.content.response, dict)
                                    else {"response": tool_response.content.response}
                                )
                                await ReviewAgentChatsRepository.update_chat(
                                    chat_id=corresp_tool_request.id,
                                    update_data=ReviewAgentChatUpdateRequest(
                                        message_data=corresp_tool_request.message_data
                                    ),
                                )

                        # Submit the tool use response to the LLM
                        current_turn_response = await self.llm_handler.start_llm_query(
                            session_id=session_id,
                            tools=tools_to_use,
                            conversation_turns=self._get_conversation_turns_from_chat(chat_dto_list),
                            prompt_feature=prompt_feature,
                            llm_model=self.model,
                            prompt_vars=prompt_vars,
                        )
                        if not isinstance(current_turn_response, NonStreamingParsedLLMCallResponse):
                            raise ValueError(
                                f"LLM Response is not of type NonStreamingParsedLLMCallResponse: {current_turn_response}"
                            )
                        current_response = current_turn_response
                        iteration_count += 1

            if iteration_count > max_iterations:
                AppLogger.log_error(
                    f"Maximum number of iterations ({max_iterations}) reached for agent {self.agent_name}"
                )
                last_pass_result = {"comments": []}

        return AgentRunResult(
            agent_result=last_pass_result,
            prompt_tokens_exceeded=False,
            agent_name=self.agent_name,
            agent_type=self.agent_type,
            model=self.model,
            tokens_data=tokens_data,
            display_name=self.get_display_name(),
        )

    def get_tools_for_review(self, prompt_handler: BasePrompt) -> List[ConversationTool]:
        """
        Get the appropriate tools for the review based on whether tools are disabled.

        Args:
            prompt_handler: The prompt handler instance

        Returns:
            List of tools to use for the review
        """
        if getattr(prompt_handler, "disable_tools", False):
            # When tools are disabled, only use the parse_final_response tool
            return [PARSE_FINAL_RESPONSE]
        return self.tool_request_manager.get_tools()
