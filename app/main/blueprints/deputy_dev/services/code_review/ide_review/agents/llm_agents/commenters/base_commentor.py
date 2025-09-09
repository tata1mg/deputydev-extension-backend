from typing import Any, Dict, List, Optional

from app.backend_common.utils.tool_response_parser import LLMResponseFormatter
from app.main.blueprints.deputy_dev.models.dto.ide_reviews_comment_dto import IdeReviewsCommentDTO
from app.main.blueprints.deputy_dev.models.dto.review_agent_chats_dto import (
    ActorType,
    MessageType,
    ReviewAgentChatCreateRequest,
    ReviewAgentChatDTO,
    ReviewAgentChatUpdateRequest,
    TextMessageData,
    ToolUseMessageData,
)
from app.main.blueprints.deputy_dev.models.dto.user_agent_dto import UserAgentDTO
from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import (
    AgentRunResult,
)
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.deputy_dev.services.code_review.common.tools.constants.tools_fallback import (
    EXCEPTION_RAISED_FALLBACK_EXTENSION,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.base_code_review_agent import (
    BaseCodeReviewAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.context.ide_review_context_service import (
    IdeReviewContextService,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.tools.parse_final_response import (
    PARSE_FINAL_RESPONSE,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.tools.tool_request_manager import (
    ToolRequestManager,
)
from app.main.blueprints.deputy_dev.services.repository.ide_reviews_comments.repository import IdeCommentRepository
from app.main.blueprints.deputy_dev.services.repository.review_agent_chats.repository import ReviewAgentChatsRepository
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
    ContentBlockCategory,
    LLModels,
    ToolUseRequestData,
    ToolUseResponseContent,
    ToolUseResponseData,
)
from deputydev_core.llm_handler.prompts.base_prompt import BasePrompt
from deputydev_core.services.chunking.chunk_info import ChunkInfo
from deputydev_core.services.chunking.utils.snippet_renderer import render_snippet_array
from deputydev_core.utils.app_logger import AppLogger


class BaseCommenterAgent(BaseCodeReviewAgent):
    is_dual_pass: bool
    prompt_features: List[PromptFeatures]

    def __init__(
        self,
        context_service: IdeReviewContextService,
        llm_handler: LLMHandler[PromptFeatures],
        model: LLModels,
        user_agent_dto: Optional[UserAgentDTO] = None,
    ) -> None:
        super().__init__(context_service, llm_handler, model)
        self.agent_id = user_agent_dto.id
        self.agent_name = user_agent_dto.agent_name
        self.display_name = user_agent_dto.display_name or self.agent_type.value
        self.agent_setting = {
            "agent_id": user_agent_dto.id,
            "display_name": user_agent_dto.display_name or self.agent_type.value,
            "objective": user_agent_dto.objective,
            "custom_prompt": user_agent_dto.custom_prompt,
            "confidence_score": user_agent_dto.confidence_score,
        }

        self.tool_request_manager = ToolRequestManager(context_service=self.context_service)
        self.review_agent_chats: List[ReviewAgentChatDTO] = []
        self.prompt_vars = {}

    def agent_relevant_chunk(self, relevant_chunks: Dict[str, Any]) -> str:
        relevant_chunks_index = relevant_chunks["relevant_chunks_mapping"][self.agent_id]
        agent_relevant_chunks: List[ChunkInfo] = []
        for index in relevant_chunks_index:
            agent_relevant_chunks.append(relevant_chunks["relevant_chunks"][index])
        return render_snippet_array(agent_relevant_chunks)

    async def required_prompt_variables(self, last_pass_result: Optional[Any] = None) -> Dict[str, Optional[str]]:
        return {
            "PULL_REQUEST_DIFF": await self.context_service.get_pr_diff(append_line_no_info=True),
            "PR_DIFF_WITHOUT_LINE_NUMBER": await self.context_service.get_pr_diff(),
            "AGENT_OBJECTIVE": self.agent_setting.get("objective", ""),
            "CUSTOM_PROMPT": self.agent_setting.get("custom_prompt") or "",
            "AGENT_NAME": self.agent_type.value,
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

    async def run_agent(self, session_id: int, payload: Optional[Dict[str, Any]] = None) -> AgentRunResult:
        """
        Run the agent and return the agent run result.
        This method now supports single-iteration flow based on payload type.

        Args:
            session_id: The session ID.
            payload: Optional payload containing type and other parameters.

        Returns:
            AgentRunResult: The agent run result.
        """
        payload = payload or {}
        request_type = payload.get("type")

        # firstly, seed the current_agent_chats array
        current_chat_data = await ReviewAgentChatsRepository.get_chats_by_agent_id_and_session(
            session_id=session_id, agent_id=str(self.agent_id)
        )
        self.review_agent_chats = current_chat_data if current_chat_data else []

        if request_type == "query":
            return await self._handle_query_request(session_id, payload)
        elif request_type == "tool_use_response" or request_type == "tool_use_failed":
            return await self._handle_tool_use_response(session_id, payload)
        else:
            raise ValueError(f"Invalid request type: {request_type}")

    async def _handle_query_request(self, session_id: int, payload: Dict[str, Any]) -> AgentRunResult:
        """
        Handle initial query request.

        Args:
            session_id: The session ID.
            payload: The request payload.

        Returns:
            AgentRunResult: The agent run result.
        """
        tokens_data: Dict[str, Dict[str, Any]] = {}

        # Use first prompt feature for single iteration
        prompt_feature = self.prompt_features[0]

        # Check if the token limit has been exceeded
        prompt_vars = await self.required_prompt_variables()
        self.prompt_vars = prompt_vars
        prompt_handler = self.llm_handler.prompt_handler_map.get_prompt(model_name=self.model, feature=prompt_feature)(
            prompt_vars
        )
        user_and_system_messages = prompt_handler.get_prompt()
        current_tokens_data = self.get_tokens_data(user_and_system_messages)
        token_limit_exceeded = self.has_exceeded_token_limit(user_and_system_messages)

        token_key = f"{self.agent_name}_QUERY"
        tokens_data[token_key] = current_tokens_data

        if token_limit_exceeded:
            # TODO what to return in case of limit exceed
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
        self.review_agent_chats.append(cached_chat)

        # create the review agent chat
        query_chat = await ReviewAgentChatsRepository.create_chat(
            ReviewAgentChatCreateRequest(
                session_id=session_id,
                agent_id=str(self.agent_id),
                actor=ActorType.REVIEW_AGENT,
                message_type=MessageType.TEXT,
                message_data=TextMessageData(text=user_and_system_messages.user_message),
                metadata={},
            )
        )

        self.review_agent_chats.append(query_chat)

        # Initial query to the LLM
        llm_response = await self.llm_handler.start_llm_query(
            session_id=session_id,
            prompt_feature=prompt_feature,
            llm_model=self.model,
            prompt_vars=prompt_vars,
            tools=tools_to_use,
            conversation_turns=self._get_conversation_turns_from_chat(self.review_agent_chats),
        )

        if not isinstance(llm_response, NonStreamingParsedLLMCallResponse):
            raise ValueError(f"LLM Response is not of type NonStreamingParsedLLMCallResponse: {llm_response}")

        tokens_data[token_key].update(
            {
                "input_tokens": llm_response.usage.input,
                "output_tokens": llm_response.usage.output,
            }
        )

        # Process the LLM response
        return await self._process_llm_response(llm_response, session_id, tools_to_use, prompt_handler, tokens_data)

    async def _handle_tool_use_response(self, session_id: int, payload: Dict[str, Any]) -> AgentRunResult:
        """
        Handle tool use response request.

        Args:
            session_id: The session ID.
            payload: The request payload containing tool use response.

        Returns:
            AgentRunResult: The agent run result.
        """
        tool_response = payload.get("tool_use_response")
        if not tool_response:
            raise ValueError("tool_use_response is required in payload")

        tool_name = payload.get("tool_use_response").get("tool_name")
        tool_use_id = payload.get("tool_use_response").get("tool_use_id")
        tool_use_failed = payload.get("type") == "tool_use_failed" or payload.get("tool_use_failed", False)

        if not tool_use_failed:
            if tool_name == "focused_snippets_searcher":
                tool_response = {
                    "chunks": [
                        ChunkInfo(**chunk).get_xml()
                        for search_response in tool_response["batch_chunks_search"]["response"]
                        for chunk in search_response["chunks"]
                    ],
                }
            elif tool_name == "iterative_file_reader":
                markdown = LLMResponseFormatter.format_iterative_file_reader_response(tool_response["response"]["data"])
                tool_response = {"Tool Response": markdown}
            elif tool_name == "grep_search":
                tool_response = {
                    "matched_contents": "".join(
                        [
                            f"<match_obj>{ChunkInfo(**matched_block['chunk_info']).get_xml()}"
                            f"<match_line>{', '.join(map(str, matched_block['matched_line']))}</match_line></match_obj>"
                            for matched_block in tool_response["response"]
                        ]
                    ),
                }
        else:
            if tool_name not in {"replace_in_file", "write_to_file"}:
                error_response = {
                    "error_message": EXCEPTION_RAISED_FALLBACK_EXTENSION.format(
                        tool_name=tool_name,
                        error_type=tool_response.get("error_type", "Unknown"),
                        error_message=tool_response.get("error_message", "An error occurred while using the tool."),
                    )
                }
                tool_response = error_response

            # Build the ToolUseResponseData
        tool_use_response = ToolUseResponseData(
            content=ToolUseResponseContent(
                tool_name=tool_name,
                tool_use_id=tool_use_id,
                response=tool_response,
            )
        )

        # store the tool response in the review_agent_chats
        last_chat = self.review_agent_chats[-1] if self.review_agent_chats else None
        if (
            last_chat
            and last_chat.message_data.message_type == MessageType.TOOL_USE
            and last_chat.message_data.tool_use_id == tool_use_id
        ):
            last_chat.message_data.tool_response = tool_use_response.content.response
            await ReviewAgentChatsRepository.update_chat(
                chat_id=last_chat.id, update_data=ReviewAgentChatUpdateRequest(message_data=last_chat.message_data)
            )

        # Get tools and prompt handler
        prompt_vars = await self.required_prompt_variables()
        prompt_feature = self.prompt_features[0]  # Use first prompt feature for tool responses
        prompt_handler = self.llm_handler.prompt_handler_map.get_prompt(model_name=self.model, feature=prompt_feature)(
            prompt_vars
        )
        tools_to_use = self.get_tools_for_review(prompt_handler)

        # Submit the tool use response to the LLM
        current_response = await self.llm_handler.start_llm_query(
            session_id=session_id,
            tools=tools_to_use,
            conversation_turns=self._get_conversation_turns_from_chat(self.review_agent_chats),
            prompt_feature=prompt_feature,
            llm_model=self.model,
            prompt_vars=prompt_vars,
        )

        if not isinstance(current_response, NonStreamingParsedLLMCallResponse):
            raise ValueError("Invalid LLM response")

        # Process the LLM response
        return await self._process_llm_response(current_response, session_id, tools_to_use, prompt_handler, {})

    async def _process_llm_response(  # noqa: C901
        self,
        llm_response: NonStreamingParsedLLMCallResponse,
        session_id: int,
        tools_to_use: List[ConversationTool],
        prompt_handler: Any,
        tokens_data: Dict[str, Dict[str, Any]],
    ) -> AgentRunResult:
        """
        Process LLM response and handle different response types.

        Args:
            llm_response: The LLM response.
            session_id: The session ID.
            tools_to_use: List of tools available.
            prompt_handler: The prompt handler instance.
            tokens_data: Token usage data.

        Returns:
            AgentRunResult: The agent run result.
        """
        # Check for parse_final_response
        if self.tool_request_manager.is_final_response(llm_response):
            try:
                final_response = self.tool_request_manager.extract_final_response(llm_response)
                for content_block in llm_response.parsed_content:
                    if (
                        hasattr(content_block, "type")
                        and content_block.type == ContentBlockCategory.TOOL_USE_REQUEST
                        and isinstance(content_block, ToolUseRequestData)
                        and content_block.content.tool_name == "parse_final_response"
                    ):
                        new_tool_request_chat = await ReviewAgentChatsRepository.create_chat(
                            ReviewAgentChatCreateRequest(
                                session_id=session_id,
                                actor=ActorType.ASSISTANT,
                                message_type=MessageType.TOOL_USE,
                                message_data=ToolUseMessageData(
                                    tool_name=content_block.content.tool_name,
                                    tool_use_id=content_block.content.tool_use_id,
                                    tool_input=content_block.content.tool_input,
                                ),
                                metadata={},
                                agent_id=str(self.agent_id),
                            )
                        )
                        self.review_agent_chats.append(new_tool_request_chat)

                await self._save_comments_to_db(final_response)
                return AgentRunResult(
                    agent_result={"status": "success", "message": "Review completed successfully"},
                    prompt_tokens_exceeded=False,
                    agent_name=self.agent_name,
                    agent_type=self.agent_type,
                    model=self.model,
                    tokens_data=tokens_data,
                    display_name=self.get_display_name(),
                )
            except Exception as e:  # noqa: BLE001
                AppLogger.log_error(f"Error processing parse_final_response: {e}")
                return AgentRunResult(
                    agent_result={"status": "error", "message": f"Error processing final response: {str(e)}"},
                    prompt_tokens_exceeded=False,
                    agent_name=self.agent_name,
                    agent_type=self.agent_type,
                    model=self.model,
                    tokens_data=tokens_data,
                    display_name=self.get_display_name(),
                )

        # Check for review planner response
        if self.tool_request_manager.is_review_planner_response(llm_response):
            try:
                for content_block in llm_response.parsed_content:
                    if (
                        hasattr(content_block, "type")
                        and content_block.type == ContentBlockCategory.TOOL_USE_REQUEST
                        and isinstance(content_block, ToolUseRequestData)
                        and content_block.content.tool_name == "pr_review_planner"
                    ):
                        # store the agent chats
                        turn_chat = await ReviewAgentChatsRepository.create_chat(
                            ReviewAgentChatCreateRequest(
                                session_id=session_id,
                                actor=ActorType.ASSISTANT,
                                message_type=MessageType.TOOL_USE,
                                message_data=ToolUseMessageData(
                                    tool_name=content_block.content.tool_name,
                                    tool_use_id=content_block.content.tool_use_id,
                                    tool_input=content_block.content.tool_input,
                                ),
                                metadata={},
                                agent_id=str(self.agent_id),
                            )
                        )
                        self.review_agent_chats.append(turn_chat)
                review_plan = await self.tool_request_manager.process_review_planner_response(llm_response, session_id)
                # Submit the review plan response to the LLM
                tool_use_response = ToolUseResponseData(
                    content=ToolUseResponseContent(
                        tool_name="pr_review_planner",
                        tool_use_id=llm_response.parsed_content[0].content.tool_use_id,
                        response=review_plan or {},
                    )
                )
                last_chat = self.review_agent_chats[-1]
                if isinstance(last_chat.message_data, ToolUseMessageData):
                    last_chat.message_data.tool_response = (
                        tool_use_response.content.response
                        if isinstance(tool_use_response.content.response, dict)
                        else {"response": tool_use_response.content.response}
                    )
                await ReviewAgentChatsRepository.update_chat(
                    last_chat.id, update_data=ReviewAgentChatUpdateRequest(message_data=last_chat.message_data)
                )
                current_response = await self.llm_handler.start_llm_query(
                    session_id=session_id,
                    tools=tools_to_use,
                    conversation_turns=self._get_conversation_turns_from_chat(self.review_agent_chats),
                    prompt_feature=self.prompt_features[0],
                    llm_model=self.model,
                    prompt_vars=self.prompt_vars,
                )
                # Recursively process the new response
                if not isinstance(current_response, NonStreamingParsedLLMCallResponse):
                    raise ValueError(f"Unexpected response type: {type(current_response)}")

                return await self._process_llm_response(
                    current_response, session_id, tools_to_use, prompt_handler, tokens_data
                )
            except Exception as e:  # noqa: BLE001
                AppLogger.log_error(f"Error processing pr_review_planner: {e}")
                return AgentRunResult(
                    agent_result={"status": "error", "message": f"Error processing review planner: {str(e)}"},
                    prompt_tokens_exceeded=False,
                    agent_name=self.agent_name,
                    agent_type=self.agent_type,
                    model=self.model,
                    tokens_data=tokens_data,
                    display_name=self.get_display_name(),
                )

        # Parse for other tool use requests
        tool_request = self.tool_request_manager.parse_tool_use_request(llm_response)
        # store the tool request in the agent_chats_db
        if tool_request:
            current_turn = await ReviewAgentChatsRepository.create_chat(
                ReviewAgentChatCreateRequest(
                    session_id=session_id,
                    actor=ActorType.ASSISTANT,
                    message_type=MessageType.TOOL_USE,
                    message_data=ToolUseMessageData(
                        tool_name=tool_request.get("tool_name"),
                        tool_use_id=tool_request.get("tool_use_id"),
                        tool_input=tool_request.get("tool_input"),
                    ),
                    metadata={},
                    agent_id=str(self.agent_id),
                )
            )

            self.review_agent_chats.append(current_turn)

            # Return tool request details to frontend
            return AgentRunResult(
                agent_result=tool_request,
                prompt_tokens_exceeded=False,
                agent_name=self.agent_name,
                agent_type=self.agent_type,
                model=self.model,
                tokens_data=tokens_data,
                display_name=self.get_display_name(),
            )

        # No tool use request found - provide fallback
        return AgentRunResult(
            agent_result={"status": "error", "message": "No valid tool use request found in LLM response"},
            prompt_tokens_exceeded=False,
            agent_name=self.agent_name,
            agent_type=self.agent_type,
            model=self.model,
            tokens_data=tokens_data,
            display_name=self.get_display_name(),
        )

    async def _save_comments_to_db(self, final_response: Dict[str, Any]) -> None:
        """
        Save the final LLM comments to the database as IdeReviewsCommentDTOs.
        """
        comments = final_response.get("comments", [])
        review_id = self.context_service.review_id
        comments_to_insert = []

        for comment in comments:
            # comment is an instance of LLMCommentData
            # Use dummy values for title and tag as requested
            # For agents, use buckets if available, else fallback to self.agent_id
            if hasattr(comment, "buckets") and comment.buckets:
                agents = [UserAgentDTO(id=agent.agent_id) for agent in comment.buckets]
            else:
                agents = [UserAgentDTO(id=self.agent_id)]

            comment_dto = IdeReviewsCommentDTO(
                review_id=review_id,
                title=comment.title,
                comment=comment.comment,
                confidence_score=comment.confidence_score,
                rationale=comment.rationale,
                corrective_code=comment.corrective_code,
                file_path=comment.file_path,
                line_hash="",  # If you have a way to compute line_hash, fill it here
                line_number=int(comment.line_number),
                tag=comment.tag,
                is_valid=True,
                agents=agents,
            )
            comments_to_insert.append(comment_dto)

        if comments_to_insert:
            await IdeCommentRepository.insert_comments(comments_to_insert)
