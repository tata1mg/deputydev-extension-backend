import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, Union

from pydantic import ValidationError
from sanic.log import logger
from torpedo import CONFIG, Task

from app.common.services.openai.client import LLMClient
from app.common.utils.app_utils import (
    build_openai_conversation_message,
    get_task_response,
    get_token_count,
)
from app.common.utils.log_time import log_time
from app.main.blueprints.deputy_dev.constants import LLMModels, PRReviewExperimentSet
from app.main.blueprints.deputy_dev.constants.constants import PrStatusTypes, TokenTypes
from app.main.blueprints.deputy_dev.constants.prompts.v1.system_prompts import (
    SCRIT_SUMMARY_PROMPT,
)
from app.main.blueprints.deputy_dev.constants.repo import VCSTypes
from app.main.blueprints.deputy_dev.models.code_review_request import CodeReviewRequest
from app.main.blueprints.deputy_dev.models.repo import PullRequestResponse
from app.main.blueprints.deputy_dev.services.atlassian.confluence.confluence_manager import (
    ConfluenceManager,
)
from app.main.blueprints.deputy_dev.services.atlassian.jira.jira_manager import (
    JiraManager,
)
from app.main.blueprints.deputy_dev.services.chunking.chunk_parsing_utils import (
    get_chunks,
    render_snippet_array,
)
from app.main.blueprints.deputy_dev.services.code_review.post_processors.pr_review_post_processor import (
    PRReviewPostProcessor,
)
from app.main.blueprints.deputy_dev.services.code_review.pre_processors.pr_review_pre_processor import (
    PRReviewPreProcessor,
)
from app.main.blueprints.deputy_dev.services.comment.base_comment import BaseComment
from app.main.blueprints.deputy_dev.services.comment.comment_factory import (
    CommentFactory,
)
from app.main.blueprints.deputy_dev.services.context_var import identifier
from app.main.blueprints.deputy_dev.services.pr.pr_service import PRService
from app.main.blueprints.deputy_dev.services.prompt.prmopt_service import PromptService
from app.main.blueprints.deputy_dev.services.repo.base_repo import BaseRepo
from app.main.blueprints.deputy_dev.services.repo.repo_factory import RepoFactory
from app.main.blueprints.deputy_dev.services.search import perform_search
from app.main.blueprints.deputy_dev.services.tiktoken import TikToken
from app.main.blueprints.deputy_dev.utils import (
    append_line_numbers,
    format_code_blocks,
    get_filtered_response,
    get_foundation_model_name,
)

NO_OF_CHUNKS = CONFIG.config["CHUNKING"]["NUMBER_OF_CHUNKS"]


class PRReviewManager:
    """Manager for processing Pull Request reviews."""

    @classmethod
    async def handle_event(cls, data: Dict[str, Any]) -> None:
        # Although we will be receiving validated payload, this is just an edge case handling, where
        # someone was able to manually push invalid message to SQS, we will check the incoming SQS message
        # if it's fine then we start the PR review process, otherwise we log the invalid payload and purge the message
        try:
            CodeReviewRequest(**data)
            logger.info("Received SQS Message: {}".format(data))
            await cls.process_pr_review(data=data)
        except ValidationError as e:
            logger.error(f"Received Invalid SQS Message - {data}: {e}")

    @staticmethod
    def set_identifier(value: str):
        """Set repo_name or any other value to the contextvar identifier

        Args:
            value (str): value to set for the identifier
        """
        identifier.set(value)

    @classmethod
    @log_time
    async def process_pr_review(cls, data: Dict[str, Any]) -> None:
        """Process a Pull Request review asynchronously.

        Args:
            data (Dict[str, Any]): Dictionary containing necessary data for processing the review.
                Expected keys: 'repo_name', 'branch', 'vcs_type', 'pr_id', 'confidence_score'.
        Returns:
            None
        """
        repo_service, comment_service = await cls.initialise_services(data)
        pr_dto = None
        try:
            tokens_data, execution_start_time = None, datetime.now()
            experiment_set, pr_dto = await PRReviewPreProcessor(repo_service, comment_service).pre_process_pr()
            if experiment_set != PRReviewExperimentSet.ReviewTest.value:
                return
            llm_comments, tokens_data, meta_info_to_save = await cls.review_pr(
                repo_service, comment_service, data["prompt_version"]
            )
            meta_info_to_save["execution_start_time"] = execution_start_time
            await PRReviewPostProcessor.post_process_pr(pr_dto, llm_comments, tokens_data, meta_info_to_save)
            logger.info(f"Completed PR review for pr id - {repo_service.pr_id}, repo_service - {data.get('repo_name')}")
        except Exception as ex:
            # if PR is inserted in db then only we will update status
            if pr_dto:
                await PRService.db_update(
                    payload={
                        "review_status": PrStatusTypes.FAILED.value,
                    },
                    filters={"id": pr_dto.id},
                )
            logger.error(
                f"PR review failed for pr - {repo_service.pr_id}, repo_name - {data.get('repo_name')} "
                f"exception {ex}"
            )
        finally:
            repo_service.delete_repo()

    @classmethod
    async def review_pr(cls, repo_service: BaseRepo, comment_service: BaseComment, prompt_version):
        pr_diff = await repo_service.get_pr_diff()
        relevant_chunk, embedding_input_tokens = await cls.get_relevant_chunk(repo_service, pr_diff)

        llm_response, pr_summary, tokens_data, meta_info_to_save = await cls.parallel_pr_review_with_gpt_models(
            await repo_service.get_pr_diff(), repo_service.pr_details, relevant_chunk, prompt_version=prompt_version
        )

        tokens_data[TokenTypes.EMBEDDING.value] = embedding_input_tokens
        if pr_summary:
            await comment_service.create_pr_comment(pr_summary, LLMModels.FoundationModel.value)

        if not llm_response.get("finetuned_comments") and not llm_response.get("foundation_comments"):
            # Add a "Looks Good to Me" comment to the Pull Request if no comments meet the threshold
            await comment_service.create_pr_comment("LGTM!!", LLMModels.FoundationModel.value)
        else:
            # parallel tasks to Post fine tuned and foundation comments
            await comment_service.post_bots_comments(llm_response)
        return llm_response, tokens_data, meta_info_to_save

    @classmethod
    async def initialise_services(cls, data: dict):
        cls.set_identifier(data.get("repo_name"))
        vcs_type = data.get("vcs_type", VCSTypes.bitbucket.value)
        repo_name, pr_id, workspace, scm_workspace_id = (
            data.get("repo_name"),
            data.get("pr_id"),
            data.get("workspace"),
            data.get("workspace_id"),
        )
        repo_service = await RepoFactory.repo(
            vcs_type=vcs_type, repo_name=repo_name, pr_id=pr_id, workspace=workspace, workspace_id=scm_workspace_id
        )
        comment_service = await CommentFactory.comment(
            vcs_type=vcs_type, repo_name=repo_name, pr_id=pr_id, workspace=workspace, pr_details=repo_service.pr_details
        )
        return repo_service, comment_service

    @staticmethod
    async def create_user_message(pr_diff: str, pr_detail: PullRequestResponse, relevant_chunk: str) -> tuple:
        """
        Creates the user message for the OpenAI chat completion API.

        Args:
            pr_diff (str): The diff of the pull request.
            pr_detail (str): Details of the pull request including title and description.
            relevant_chunk (str): Relevant chunks of code for the review.

        Returns:
            tuple: PR review context, PR summary context.
        """
        jira_manager = JiraManager(issue_id=pr_detail.issue_id)
        user_story_description = await jira_manager.get_description_text()
        confluence_doc_id, confluence_data = await jira_manager.get_confluence_link_attached(), None
        if confluence_doc_id:
            confluence_data = await ConfluenceManager(confluence_doc_id).get_description_text()
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
                f"\n Following is the additional user story "
                f"description primarily present in tags - {confluence_data}\n"
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
            TokenTypes.PR_REVIEW_USER_PROMPT.value: tik_token.count(pr_review_context or "", model=model),
        }
        meta_info = {
            "issue_id": pr_detail.issue_id,
            "confluence_doc_id": confluence_doc_id,
        }
        return pr_review_context, pr_summary_context, user_context_tokens, meta_info

    @classmethod
    async def parallel_pr_review_with_gpt_models(
        cls, pr_diff: str, pr_detail: PullRequestResponse, relevant_chunk: str, prompt_version: str
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
        pr_review_context, pr_summary_context, tokens_info, meta_info = await cls.create_user_message(
            pr_diff_with_line_numbers, pr_detail, relevant_chunk
        )

        # using tiktoken to count the total tokens consumed by characters from relevant chunks and pr diff

        cls.log_token_counts(pr_diff_with_line_numbers, relevant_chunk, pr_review_context)
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
                cls.get_client_pr_comments(
                    conversation_message=pr_review_conversation_message,
                    model="FINETUNED_SCRIT_MODEL",
                    client_type="openai",
                    max_retry=2,
                ),
                result_key="finetuned_model",
            ),
            # PR review by scrit model
            Task(
                cls.get_client_pr_comments(
                    conversation_message=pr_review_conversation_message,
                    model="SCRIT_MODEL",
                    max_retry=2,
                    client_type="openai",
                ),
                result_key="foundation_model",
            ),
            # PR summarisation by scrit model
            Task(
                cls.get_client_pr_comments(
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
            "finetuned_comments": task_response.get("finetuned_model", {}).get("comments", []),
            "foundation_comments": task_response.get("foundation_model", {}).get("comments", []),
        }

        # extract tokens data
        new_tokens_data = cls.extract_tokens_post_pr_review(task_response)
        tokens_info.update(new_tokens_data)
        tokens_info[TokenTypes.PR_REVIEW_SYSTEM_PROMPT.value] = get_token_count(pr_review_system_prompt)
        tokens_info[TokenTypes.PR_REVIEW_USER_PROMPT.value] = get_token_count(pr_review_context)
        return combined_comments, foundation_model_pr_summarisation, tokens_info, meta_info

    @classmethod
    def extract_tokens_post_pr_review(cls, task_response: dict):
        tokens_data = {
            TokenTypes.PR_REVIEW_MODEL_INPUT.value: task_response.get("foundation_model", {}).get("prompt_tokens"),
            TokenTypes.PR_REVIEW_MODEL_OUTPUT.value: task_response.get("foundation_model", {}).get("completion_tokens"),
            TokenTypes.PR_SUMMARY_MODEL_INPUT.value: task_response.get("foundation_model_pr_summarisation", {}).get(
                "prompt_tokens"
            ),
            TokenTypes.PR_SUMMARY_MODEL_OUTPUT.value: task_response.get("foundation_model_pr_summarisation", {}).get(
                "completion_tokens"
            ),
        }

        return tokens_data

    @classmethod
    async def get_client_pr_comments(
        cls, conversation_message, model, client_type, response_type="json_object", max_retry=2
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
        client = LLMClient(client_type=client_type)
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
                            "pr_summary": format_code_blocks(pr_summary),
                            "completion_tokens": output_tokens.completion_tokens,
                            "prompt_tokens": output_tokens.prompt_tokens,
                        }

                    # In case of PR review comments decode json, filter and format the comments
                    pr_review_response = json.loads(response.content)
                    if "comments" in pr_review_response:
                        filtered_comments = cls.filtered_comments(
                            pr_comments=pr_review_response,
                            confidence_filter_score=model_config.get("CONFIDENCE_SCORE"),
                        )
                        pr_comments = {
                            "comments": filtered_comments,
                            "completion_tokens": output_tokens.completion_tokens,
                            "prompt_tokens": output_tokens.prompt_tokens,
                        }
                        return pr_comments

                except json.JSONDecodeError as e:
                    logger.error("JSON decode error while decoding PR review comments data: {}".format(e))
                except Exception as e:
                    logger.error("Exception occurred while fetching data from openai: {}".format(e))
                await asyncio.sleep(0.2)

        return (
            {
                "pr_summary": pr_summary,
                "completion_tokens": output_tokens.completion_tokens,
                "prompt_token": output_tokens.prompt_tokens,
            }
            if response_type == "text"
            else pr_comments
        )

    @classmethod
    def filtered_comments(cls, pr_comments: dict, confidence_filter_score: float) -> list:
        """
        Filters the comments based on the confidence score.

        Args:
            pr_comments (dict): OpenAI PR comments.
            confidence_filter_score (float): Confidence score threshold to filter comments.

        Returns:
            list: Filtered comments.
        """
        filtered_comments = []
        for comment in pr_comments.get("comments"):
            if get_filtered_response(comment, confidence_filter_score):
                comment["comment"] = format_code_blocks(comment.get("comment"))
                filtered_comments.append(comment)
        return filtered_comments

    @staticmethod
    def log_token_counts(pr_diff: str, relevant_chunk: str, reveiw_context: str):
        pr_diff_token_count = get_token_count(pr_diff)
        relevant_chunk_token_count = get_token_count(relevant_chunk)
        pr_review_context_token_count = get_token_count(reveiw_context)
        logger.info(
            f"PR diff token count - {pr_diff_token_count}, relevant Chunk token count - {relevant_chunk_token_count}, total token count - {pr_review_context_token_count}"
        )

    @classmethod
    async def get_relevant_chunk(cls, repo, diff):
        # clone the repo
        all_chunks, all_docs = await get_chunks(repo.repo_dir)
        logger.info("Completed chunk creation")

        # Perform a search based on the diff content to find relevant chunks
        content_to_lexical_score_list, input_tokens = await perform_search(
            all_docs=all_docs, all_chunks=all_chunks, query=diff
        )
        logger.info("Completed lexical and vector search")

        # Rank relevant chunks based on lexical scores
        ranked_snippets_list = sorted(
            all_chunks,
            key=lambda chunk: content_to_lexical_score_list[chunk.denotation],
            reverse=True,
        )[:NO_OF_CHUNKS]

        # Render relevant chunks into a single snippet
        relevant_chunk = render_snippet_array(ranked_snippets_list)
        return relevant_chunk, input_tokens
