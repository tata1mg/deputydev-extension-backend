import json
from typing import Any, Dict, List, Optional

from deputydev_core.services.chunking.chunk_info import ChunkInfo
from deputydev_core.services.chunking.utils.snippet_renderer import render_snippet_array
from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.context_vars import get_context_value
from torpedo import CONFIG

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.backend_common.services.llm.dataclasses.main import (
    NonStreamingParsedLLMCallResponse,
)
from app.backend_common.services.llm.handler import LLMHandler
from app.main.blueprints.deputy_dev.services.code_review.agents.base_code_review_agent import (
    BaseCodeReviewAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.agents.dataclasses.main import (
    AgentRunResult,
)
from app.main.blueprints.deputy_dev.services.code_review.context.context_service import (
    ContextService,
)
from app.main.blueprints.deputy_dev.services.code_review.prompts.base_prompts.dataclasses.main import (
    LLMCommentData,
)
from app.main.blueprints.deputy_dev.services.code_review.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.deputy_dev.services.code_review.tools.tool_request_manager import (
    ToolRequestManager,
)
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
    ):
        super().__init__(context_service, is_reflection_enabled, llm_handler, model)
        self.agent_name = SettingService.helper.predefined_name_to_custom_name(self.agent_name)
        self.agent_setting = SettingService.helper.agent_setting_by_name(self.agent_name)
        self.agent_id = self.agent_setting.get("agent_id")
        self.display_name = self.agent_setting.get("display_name")
        self.tool_request_manager = ToolRequestManager()

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

    async def run_agent(self, session_id: int) -> AgentRunResult:
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
            tools_to_use = self.tool_request_manager.get_tools()

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

            # Process tool use requests iteratively
            current_response = llm_response
            max_iterations = CONFIG.config[
                "MAX_REVIEW_TOOL_ITERATIONS"
            ]  # Limit the number of iterations to prevent infinite loops
            iteration_count = 0

            while iteration_count < max_iterations:
                # Check if parse_final_response tool is used
                if self.tool_request_manager.is_final_response(current_response):
                    final_response = self.tool_request_manager.extract_final_response(current_response)
                    last_pass_result = final_response
                    break

                # Iterative tool use
                tool_use_response = await self.tool_request_manager.process_tool_use_request(
                    current_response, session_id
                )

                if tool_use_response is None:
                    print(current_response.parsed_content)
                    last_pass_result = {}
                    AppLogger.log_error(f"No tools were used for agent {self.agent_name}")
                    break

                # Submit the tool use response to the LLM
                current_response = await self.llm_handler.submit_tool_use_response(
                    session_id=session_id,
                    tool_use_response=tool_use_response,
                    tools=tools_to_use,
                    prompt_type=prompt_handler.prompt_type,
                )

                iteration_count += 1

            if iteration_count >= max_iterations:
                AppLogger.log_error(
                    f"Maximum number of iterations ({max_iterations}) reached for agent {self.agent_name}"
                )
                last_pass_result = {}

        return AgentRunResult(
            agent_result=last_pass_result,
            prompt_tokens_exceeded=False,
            agent_name=self.agent_name,
            agent_type=self.agent_type,
            model=self.model,
            tokens_data=tokens_data,
            display_name=self.get_display_name(),
        )
