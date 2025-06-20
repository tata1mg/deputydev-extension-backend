import asyncio
import json
from typing import Dict, Union

from deputydev_core.services.chunking.chunking_manager import ChunkingManger
from deputydev_core.services.repo.local_repo.managers.git_repo_service import GitRepo
from deputydev_core.services.search.dataclasses.main import SearchTypes
from deputydev_core.services.tiktoken import TikToken
from deputydev_core.utils.context_vars import get_context_value
from sanic.log import logger
from torpedo import CONFIG, Task

from app.backend_common.services.embedding.openai_embedding_manager import (
    OpenAIEmbeddingManager,
)
from app.backend_common.services.openai.openai_llm_service import OpenAILLMService
from app.backend_common.services.pr.base_pr import BasePR
from app.backend_common.services.pr.dataclasses.main import PullRequestResponse
from app.backend_common.services.repo.base_repo import BaseRepo
from app.backend_common.utils.app_utils import (
    build_openai_conversation_message,
    get_foundation_model_name,
    get_task_response,
    get_token_count,
)
from app.backend_common.utils.executor import process_executor
from app.backend_common.utils.formatting import append_line_numbers, format_code_blocks
from app.main.blueprints.deputy_dev.constants.constants import TokenTypes
from app.main.blueprints.deputy_dev.constants.prompts.v1.system_prompts import (
    SCRIT_SUMMARY_PROMPT,
)
from app.main.blueprints.deputy_dev.helpers.pr_diff_handler import PRDiffHandler
from app.main.blueprints.deputy_dev.services.code_review.context.context_service import (
    ContextService,
)
from app.main.blueprints.deputy_dev.services.prompt.prompt_service import PromptService
from app.main.blueprints.deputy_dev.utils import get_filtered_response


class SingleAgentPRReviewManager:
    def __init__(
        self,
        repo_service: BaseRepo,
        pr_service: BasePR,
        pr_diff_handler: PRDiffHandler,
        session_id: int,
        prompt_version: None,
    ):
        self.repo_service = repo_service
        self.pr_service = pr_service
        self.prompt_version = prompt_version
        self.context_service = ContextService(
            repo_service=repo_service, pr_service=pr_service, pr_diff_handler=pr_diff_handler
        )
        self.pr_diff_handler = pr_diff_handler

    async def get_code_review_comments(self):
        use_new_chunking = (
            False and get_context_value("team_id") not in CONFIG.config["TEAMS_NOT_SUPPORTED_FOR_NEW_CHUNKING"]
        )
        relevant_chunk, embedding_input_tokens = await ChunkingManger.get_relevant_chunks(
            query=await self.pr_diff_handler.get_effective_pr_diff(),
            local_repo=GitRepo(self.repo_service.repo_dir),
            use_new_chunking=use_new_chunking,
            use_llm_re_ranking=False,
            embedding_manager=OpenAIEmbeddingManager,
            chunkable_files_with_hashes={},
            search_type=SearchTypes.NATIVE,
            process_executor=process_executor,
        )
        llm_response, pr_summary, tokens_data, meta_info_to_save = await self.parallel_pr_review_with_gpt_models(
            await self.context_service.get_pr_diff(),
            self.pr_service.pr_details,
            relevant_chunk,
            prompt_version=self.prompt_version,
        )
        tokens_data[TokenTypes.EMBEDDING.value] = embedding_input_tokens
        return llm_response, pr_summary, tokens_data, meta_info_to_save

    async def parallel_pr_review_with_gpt_models(
        self, pr_diff: str, pr_detail: PullRequestResponse, relevant_chunk: str, prompt_version: str
    ) -> tuple:
        """
        Runs a thread parallely to call normal GPT-4 and fine-tuned GPT model to review the PR and provide comments.

        Args:
            pr_diff (str): Diff of the pull request.
            pr_detail (str): Details of the pull request including title and description.
            relevant_chunk (str): Relevant chunks of code for the review.

        Returns:
            Tuple[Dict, str]: Combined OpenAI PR comments filtered by confidence_filter_score and PR summary.
        """
        pr_diff_with_line_numbers = append_line_numbers(pr_diff)
        pr_review_context, pr_summary_context, tokens_info, meta_info = await self.create_user_message(
            pr_diff_with_line_numbers, pr_detail, relevant_chunk
        )

        # using tiktoken to count the total tokens consumed by characters from relevant chunks and pr diff
        pr_review_system_prompt = await PromptService.build_pr_review_prompt(prompt_version)
        pr_review_conversation_message = build_openai_conversation_message(
            system_message=pr_review_system_prompt, user_message=pr_review_context
        )
        pr_review_summarisation_converstation_message = build_openai_conversation_message(
            system_message=SCRIT_SUMMARY_PROMPT, user_message=pr_summary_context
        )

        # Create three parallel tasks to get PR reviewed by finetuned model and gpt4 model and also get the PR summarisation
        tasks = [
            # PR review by finetuned model
            Task(
                self.get_client_pr_comments(
                    conversation_message=pr_review_conversation_message,
                    model="FINETUNED_SCRIT_MODEL",
                    client_type="openai",
                    max_retry=2,
                ),
                result_key="finetuned_model",
            ),
            # PR review by scrit model
            Task(
                self.get_client_pr_comments(
                    conversation_message=pr_review_conversation_message,
                    model="SCRIT_MODEL",
                    max_retry=2,
                    client_type="openai",
                ),
                result_key="foundation_model",
            ),
            # PR summarisation by scrit model
            Task(
                self.get_client_pr_comments(
                    conversation_message=pr_review_summarisation_converstation_message,
                    model="SCRIT_MODEL",
                    max_retry=2,
                    client_type="openai",
                    response_type="text",
                ),
                result_key="foundation_model_pr_summarisation",
            ),
        ]
        task_response = await get_task_response(tasks)
        # combine finetuned and gpt4 filtered comments
        foundation_model_pr_summarisation = task_response.get("foundation_model_pr_summarisation", {}).get("pr_summary")
        combined_comments = {
            "foundation_comments": task_response.get("foundation_model", {}).get("comments", []),
            "summary": foundation_model_pr_summarisation,
        }

        # extract tokens data
        agents_tokens = self.create_agents_tokens(task_response)

        return combined_comments, agents_tokens, meta_info

    async def create_user_message(self, pr_diff: str, pr_detail: PullRequestResponse, relevant_chunk: str) -> tuple:
        """
        Creates the user message for the OpenAI chat completion API.

        Args:
            pr_diff (str): The diff of the pull request.
            pr_detail (str): Details of the pull request including title and description.
            relevant_chunk (str): Relevant chunks of code for the review.

        Returns:
            tuple: PR review context, PR summary context.
        """
        user_story_description = await self.context_service.get_user_story()
        confluence_data = await self.context_service.get_confluence_doc()
        confluence_doc_id = self.context_service.get_confluence_id()

        pr_review_context = (
            "You are a great code reviewer who has been given a PR to review along with some relevant"
            " chunks of code and user story description. Relevant chunks of code are enclosed within "
            "<relevant_chunks_in_repo></relevant_chunks_in_repo> tags. "
        )
        if user_story_description:
            pr_review_context += (
                f"Following is the user story "
                f"description - {user_story_description}. You should use this "
                f"to make comments around change in business logic that is not expected to do."
            )

        if confluence_data:
            pr_review_context += (
                f"\n Following is the additional user story description primarily present in tags - {confluence_data}\n"
            )

        pr_review_context += (
            f"Use the relevant chunks of code to review the PR passed. Relevant code chunks: '{relevant_chunk}, "
            f"Review this PR with Title: '{pr_detail.title}', "
            f"Description: '{pr_detail.description}', "
            f"PR_diff: {pr_diff}"
        )

        pr_summary_context = f"What does the following PR do ? PR diff: {pr_diff}"
        tik_token = TikToken()
        model = get_foundation_model_name()
        user_context_tokens = {
            TokenTypes.PR_TITLE.value: tik_token.count(pr_detail.title or "", model=model),
            TokenTypes.PR_DESCRIPTION.value: tik_token.count(pr_detail.description or "", model=model),
            TokenTypes.PR_DIFF_TOKENS.value: tik_token.count(pr_diff or "", model=model),
            TokenTypes.PR_USER_STORY.value: tik_token.count(user_story_description or "", model=model),
            TokenTypes.PR_CONFLUENCE.value: tik_token.count(confluence_data or "", model=model),
            TokenTypes.RELEVANT_CHUNK.value: tik_token.count(relevant_chunk or "", model=model),
        }
        meta_info = {
            "issue_id": pr_detail.issue_id,
            "confluence_doc_id": confluence_doc_id,
        }
        return pr_review_context, pr_summary_context, user_context_tokens, meta_info

    def create_agents_tokens(
        self, tokens, task_response, pr_review_system_prompt, pr_review_context, pr_summary_context
    ):
        summary_tokens = {
            TokenTypes.PR_DIFF_TOKENS.value: tokens.get(TokenTypes.PR_DIFF_TOKENS.value),
            TokenTypes.SYSTEM_PROMPT.value: get_token_count(pr_summary_context),
            TokenTypes.USER_PROMPT.value: get_token_count(SCRIT_SUMMARY_PROMPT),
            TokenTypes.MODEL_INPUT_TOKENS.value: task_response.get("foundation_model_pr_summarisation", {}).get(
                "prompt_tokens"
            ),
            TokenTypes.MODEL_OUTPUT_TOKENS.value: task_response.get("foundation_model_pr_summarisation", {}).get(
                "completion_tokens"
            ),
        }

        tokens[TokenTypes.MODEL_INPUT_TOKENS.value] = (task_response.get("foundation_model", {}).get("prompt_tokens"),)
        tokens[TokenTypes.MODEL_OUTPUT_TOKENS.value] = (
            task_response.get("foundation_model", {}).get("completion_tokens"),
        )
        tokens[TokenTypes.SYSTEM_PROMPT.value] = get_token_count(pr_review_system_prompt)
        tokens[TokenTypes.USER_PROMPT.value] = get_token_count(pr_review_context)
        return {"foundation_comments": tokens, "summary": summary_tokens}

    async def get_client_pr_comments(
        self, conversation_message, model, client_type, response_type="json_object", max_retry=2
    ) -> Union[str, Dict]:
        """
        Makes a call to OpenAI chat completion API with a specific model and conversation messages.
        Implements a retry mechanism in case of a failed request or improper response.

        Args:
            conversation_message: System and user message object.
            model: GPT model Name defined in config file.
            client_type: llm clien we are using
            max_retry: Number of times OpenAI should be called in case of failure or improper response.

        Returns:
            Union[str, Dict] Pr summary or PR review comments
        """
        client = OpenAILLMService(client_type=client_type)
        pr_comments = {}
        pr_summary = ""
        model_config = CONFIG.config.get(model)
        output_tokens = 0
        if model_config.get("ENABLED"):
            for _ in range(max_retry):
                try:
                    response, output_tokens = await client.get_client_response(
                        conversation_message, model_config.get("MODEL"), response_type
                    )
                    # IN case of PR summary, just format the code blocks if present
                    if response_type == "text":
                        pr_summary = response.content
                        return {
                            "summary": format_code_blocks(pr_summary),
                            "completion_tokens": output_tokens.completion_tokens,
                            "prompt_tokens": output_tokens.prompt_tokens,
                            "structure_type": "text",
                            "model": model,
                        }

                    # In case of PR review comments decode json, filter and format the comments
                    pr_review_response = json.loads(response.content)
                    if "comments" in pr_review_response:
                        filtered_comments = self.filtered_comments(
                            pr_comments=pr_review_response,
                            confidence_filter_score=model_config.get("CONFIDENCE_SCORE"),
                        )
                        pr_comments = {
                            "comments": filtered_comments,
                            "completion_tokens": output_tokens.completion_tokens,
                            "prompt_tokens": output_tokens.prompt_tokens,
                            "structure_type": "json",
                        }
                        return pr_comments

                except json.JSONDecodeError as e:
                    logger.error("JSON decode error while decoding PR review comments data: {}".format(e))
                except Exception as e:
                    logger.error("Exception occurred while fetching data from openai: {}".format(e))
                await asyncio.sleep(0.2)

        return (
            {
                "response": pr_summary,
                "completion_tokens": output_tokens.completion_tokens,
                "prompt_token": output_tokens.prompt_tokens,
                "structure_type": "text",
            }
            if response_type == "text"
            else pr_comments
        )

    def filtered_comments(self, pr_comments: dict, confidence_filter_score: float) -> list:
        """
        Filters the comments based on the confidence score.

        Args:
            pr_comments (dict): OpenAI PR comments.
            confidence_filter_score (float): Confidence score threshold to filter comments.

        Returns:
            list: Filtered comments.
        """
        filtered_comments = []
        for comment in pr_comments.get("response").get("comments"):
            if get_filtered_response(comment, confidence_filter_score):
                comment["comment"] = format_code_blocks(comment.get("comment"))
                filtered_comments.append(comment)
        return filtered_comments
