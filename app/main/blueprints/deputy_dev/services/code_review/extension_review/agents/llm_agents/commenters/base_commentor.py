import json
from typing import Any, Dict, List, Optional

from deputydev_core.services.chunking.chunk_info import ChunkInfo
from deputydev_core.services.chunking.utils.snippet_renderer import render_snippet_array
from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.context_vars import get_context_value
from torpedo import CONFIG

from app.backend_common.models.dto.message_thread_dto import (
    LLModels,
    ToolUseResponseContent,
    ToolUseResponseData,
)
from app.backend_common.services.llm.dataclasses.main import (
    ConversationTool,
    NonStreamingParsedLLMCallResponse,
)
from app.backend_common.services.llm.handler import LLMHandler
from app.main.blueprints.deputy_dev.services.code_review.extension_review.agents.base_code_review_agent import (
    BaseCodeReviewAgent,
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
from app.main.blueprints.deputy_dev.services.code_review.extension_review.tools.tool_request_manager import (
    ToolRequestManager,
)
from app.main.blueprints.deputy_dev.services.setting.setting_service import (
    SettingService,
)
from app.main.blueprints.deputy_dev.services.code_review.extension_review.context.extension_context_service import (
    ExtensionContextService,
)
from app.main.blueprints.deputy_dev.utils import repo_meta_info_prompt
from app.main.blueprints.deputy_dev.models.dto.user_agent_dto import UserAgentDTO


class BaseCommenterAgent(BaseCodeReviewAgent):
    is_dual_pass: bool
    prompt_features: List[PromptFeatures]

    def __init__(
        self,
        context_service: ExtensionContextService,
        llm_handler: LLMHandler[PromptFeatures],
        model: LLModels,
        user_agent_dto: Optional[UserAgentDTO] = None,
    ):
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

        # self.agent_name = SettingService.helper.predefined_name_to_custom_name(self.agent_name)
        # self.agent_setting = SettingService.helper.agent_setting_by_name(self.agent_name)
        # self.agent_id = self.agent_setting.get("agent_id")
        # self.display_name = self.agent_setting.get("display_name")
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
            "PULL_REQUEST_TITLE": "",
            "PULL_REQUEST_DESCRIPTION": "",
            "PULL_REQUEST_DIFF": await self.context_service.get_pr_diff(append_line_no_info=True),
            "REVIEW_COMMENTS_BY_JUNIOR_DEVELOPER": last_pass_comments_str,
            "USER_STORY": "",
            "PRODUCT_RESEARCH_DOCUMENT": "",
            "PR_DIFF_WITHOUT_LINE_NUMBER": await self.context_service.get_pr_diff(),
            "AGENT_OBJECTIVE": self.agent_setting.get("objective", ""),
            "CUSTOM_PROMPT": self.agent_setting.get("custom_prompt") or "",
            "BUCKET": self.agent_setting.get("display_name"),
            "REPO_INFO_PROMPT": "",
            "AGENT_NAME": self.agent_type.value,
        }

    def get_additional_info_prompt(self, tokens_info, reflection_iteration):
        return {
            "key": self.agent_name,
            "comment_confidence_score": self.agent_setting.get("confidence_score"),
            "model": self.model,
            "tokens": tokens_info,
            "reflection_iteration": reflection_iteration,
        }

    def get_display_name(self):
        return self.agent_setting.get("display_name")

    def get_tools_for_review(self, prompt_handler) -> List[ConversationTool]:
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

        if request_type == "query":
            return await self._handle_query_request(session_id, payload)
        elif request_type == "tool_use_response":
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

        # Initial query to the LLM
        llm_response = await self.llm_handler.start_llm_query(
            session_id=session_id,
            prompt_feature=prompt_feature,
            llm_model=self.model,
            prompt_vars=prompt_vars,
            tools=tools_to_use,
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
        tool_use_response = payload.get("tool_use_response")
        if not tool_use_response:
            raise ValueError("tool_use_response is required in payload")

        # if payload.get("tool_use_response").get("tool_name") == "focused_snippets_searcher":
        #     tool_response = {
        #         "chunks": [
        #             ChunkInfo(**chunk).get_xml()
        #             for search_response in payload.get("tool_use_response").get("response")["batch_chunks_search"]["response"]
        #             for chunk in search_response["chunks"]
        #         ],
        #     }
        #
        # if payload.get("tool_use_response").get("tool_name") == "iterative_file_reader":
        #     tool_response = {
        #         "file_content_with_line_numbers": ChunkInfo(**payload.get("tool_use_response").get("response")["data"]["chunk"]).get_xml(),
        #         "eof_reached": payload.get("tool_use_response").get("response")["data"]["eof_reached"],
        #     }
        #
        # if payload.get("tool_use_response").get("tool_name") == "grep_search":
        #     tool_response = {
        #         "matched_contents": "".join(
        #             [
        #                 f"<match_obj>{ChunkInfo(**matched_block['chunk_info']).get_xml()}<match_line>{matched_block['matched_line']}</match_line></match_obj>"
        #                 for matched_block in payload.get("tool_use_response").get("response")["data"]
        #             ]
        #         ),
        #     }

        # Convert to ToolUseResponseData
        tool_use_response = ToolUseResponseData(
            content=ToolUseResponseContent(
                tool_name=tool_use_response["tool_name"],
                tool_use_id=tool_use_response["tool_use_id"],
                response="**Just call parse_final_response tool and provide the Final COMMENTS.**",
                # response=tool_use_response["response"],
            )
        )

        # Get tools and prompt handler
        prompt_vars = await self.required_prompt_variables()
        prompt_feature = self.prompt_features[0]  # Use first prompt feature for tool responses
        prompt_handler = self.llm_handler.prompt_handler_map.get_prompt(model_name=self.model, feature=prompt_feature)(
            prompt_vars
        )
        tools_to_use = self.get_tools_for_review(prompt_handler)

        # Submit the tool use response to the LLM
        current_response = await self.llm_handler.submit_tool_use_response(
            session_id=session_id,
            tool_use_response=tool_use_response,
            tools=tools_to_use,
            prompt_type=prompt_handler.prompt_type,
        )

        # Process the LLM response
        return await self._process_llm_response(current_response, session_id, tools_to_use, prompt_handler, {})

    async def _process_llm_response(
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
                # Save to DB and return success
                # TODO Save comments
                # await self._save_comments_to_db(final_response)
                return AgentRunResult(
                    agent_result={"status": "success", "message": "Review completed successfully"},
                    prompt_tokens_exceeded=False,
                    agent_name=self.agent_name,
                    agent_type=self.agent_type,
                    model=self.model,
                    tokens_data=tokens_data,
                    display_name=self.get_display_name(),
                )
            except Exception as e:
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
                print("PLANNING")
                review_plan = await self.tool_request_manager.process_review_planner_response(llm_response, session_id)
                # Submit the review plan response to the LLM
                tool_use_response = ToolUseResponseData(
                    content=ToolUseResponseContent(
                        tool_name="pr_review_planner",
                        tool_use_id=llm_response.parsed_content[0].content.tool_use_id,
                        response=review_plan,
                    )
                )
                current_response = await self.llm_handler.submit_tool_use_response(
                    session_id=session_id,
                    tool_use_response=tool_use_response,
                    tools=tools_to_use,
                    prompt_type=prompt_handler.prompt_type,
                )
                # Recursively process the new response
                return await self._process_llm_response(
                    current_response, session_id, tools_to_use, prompt_handler, tokens_data
                )
            except Exception as e:
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
        if tool_request:
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
