import asyncio
import json
import re
from typing import Any, Dict, Union

from sanic.log import logger
from torpedo import CONFIG, Task

from app.constants.constants import (
    MAX_PR_DIFF_TOKEN_LIMIT,
    PR_SIZE_TOO_BIG_MESSAGE,
    Augmentation,
    LLMModels,
)
from app.constants.repo import VCSTypes
from app.decorators.log_time import log_time
from app.modules.chunking.chunk_parsing_utils import (
    render_snippet_array,
    source_to_chunks,
)
from app.modules.clients import LLMClient
from app.modules.jira.jira_manager import JiraManager
from app.modules.repo import RepoModule
from app.modules.search import perform_search
from app.utils import (
    build_openai_conversation_message,
    format_code_blocks,
    get_filtered_response,
    get_task_response,
    get_token_count,
)

NO_OF_CHUNKS = CONFIG.config["CHUNKING"]["NUMBER_OF_CHUNKS"]


class CodeReviewManager:
    """Manager for processing Pull Request reviews."""

    @classmethod
    async def handle_event(cls, data: Dict[str, Any]) -> None:
        logger.info("Received SQS Message: {}".format(data))
        await cls.process_pr_review(data=data)

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
        # Initialize RepoModule with repository details
        repo = RepoModule(
            repo_full_name=data.get("repo_name"),
            pr_id=data.get("pr_id"),
            vcs_type=data.get("vcs_type", VCSTypes.bitbucket.value),
        )
        await repo.initialize()

        pr_id = repo.get_pr_id()
        diff = await repo.get_pr_diff()
        if diff == "":
            return logger.info(
                f"PR - {pr_id} for repo - {data.get('repo_name')} doesn't contain any valid files to review"
            )

        # Check if diff size exceeds the maximum allowable changes
        pr_diff_token_count = get_token_count(diff)
        if pr_diff_token_count > MAX_PR_DIFF_TOKEN_LIMIT:
            logger.info("PR diff token count is {}. Unable to process this request.".format(pr_diff_token_count))
            # Add a comment to the Pull Request indicating the size is too large
            comment = PR_SIZE_TOO_BIG_MESSAGE.format(
                pr_diff_token_count=pr_diff_token_count, max_token_limit=MAX_PR_DIFF_TOKEN_LIMIT
            )
            await repo.create_comment_on_pr(comment=comment, model=LLMModels.FoundationModel.value)
            return
        else:
            # clone the repo
            await repo.clone_repo()

            # Process source code into chunks and documents
            all_chunks, all_docs = source_to_chunks(repo.repo_dir)
            logger.info("Completed chunk creation")

            # Perform a search based on the diff content to find relevant chunks
            content_to_lexical_score_list = await perform_search(all_docs=all_docs, all_chunks=all_chunks, query=diff)
            logger.info("Completed lexical and vector search")

            # Rank relevant chunks based on lexical scores
            ranked_snippets_list = sorted(
                all_chunks,
                key=lambda chunk: content_to_lexical_score_list[chunk.denotation],
                reverse=True,
            )[:NO_OF_CHUNKS]

            # Render relevant chunks into a single snippet
            relevant_chunk = render_snippet_array(ranked_snippets_list)

            response, pr_summary = await cls.parallel_pr_review_with_gpt_models(diff, repo.pr_details, relevant_chunk)

            if not response.get("finetuned_comments") and not response.get("foundation_comments"):
                # Add a "Looks Good to Me" comment to the Pull Request if no comments meet the threshold
                await repo.create_comment_on_pr("LGTM!!", LLMModels.FoundationModel.value)
            else:
                # parallel tasks to Post finetuned and foundation comments
                await repo.post_bots_comments(response)

            if pr_summary:
                await repo.create_comment_on_pr(pr_summary, LLMModels.FoundationModel.value)

            # Clean up by deleting the cloned repository
            repo.delete_repo()
            logger.info(f"Completed PR review for pr id - {pr_id}, repo - {data.get('repo_name')}")
            return

    @staticmethod
    async def create_user_message(pr_diff: str, pr_detail: str, relevant_chunk: str) -> tuple:
        """
        Creates the user message for the OpenAI chat completion API.

        Args:
            pr_diff (str): The diff of the pull request.
            pr_detail (str): Details of the pull request including title and description.
            relevant_chunk (str): Relevant chunks of code for the review.

        Returns:
            tuple: PR review context, PR summary context.
        """
        user_story_description = await JiraManager(issue_id=pr_detail.issue_id).get_description_text()

        pr_review_context = "You are a great code reviewer who has been given a PR to review along with some relevant chunks of code and user story description. Relevant chunks of code are enclosed within <relevant_chunks_in_repo></relevant_chunks_in_repo> tags. "

        if user_story_description:
            pr_review_context += f"Following is the user story description - {user_story_description}. You should use this to make comments around change in business logic that is not expected to do."

        pr_review_context += (
            f"Use the relevant chunks of code to review the PR passed. Relevant code chunks: '{relevant_chunk}, "
            f"Review this PR with Title: '{pr_detail.title}', "
            f"Description: '{pr_detail.description}', "
            f"PR_diff: {pr_diff}"
        )

        pr_summary_context = f"What does the following PR do ? PR diff: {pr_diff}"

        return pr_review_context, pr_summary_context

    @classmethod
    async def parallel_pr_review_with_gpt_models(cls, pr_diff: str, pr_detail: str, relevant_chunk: str) -> list:
        """
        Runs a thread parallely to call normal GPT-4 and fine-tuned GPT model to review the PR and provide comments.

        Args:
            pr_diff (str): Diff of the pull request.
            pr_detail (str): Details of the pull request including title and description.
            relevant_chunk (str): Relevant chunks of code for the review.

        Returns:
            Tuple[Dict, str]: Combined OpenAI PR comments filtered by confidence_filter_score and PR summary.
        """

        pr_review_context, pr_summary_context = await cls.create_user_message(pr_diff, pr_detail, relevant_chunk)

        # using tiktoken to count the total tokens consumed by characters from relevant chunks and pr diff
        cls.log_token_counts(pr_diff, relevant_chunk, pr_review_context)

        pr_review_conversation_message = build_openai_conversation_message(
            system_message=Augmentation.SCRIT_PROMT.value, user_message=pr_review_context
        )
        pr_review_summarisation_converstation_message = build_openai_conversation_message(
            system_message=Augmentation.SCRIT_SUMMARY_PROMPT.value, user_message=pr_summary_context
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
        foundation_model_pr_summarisation = task_response.get("foundation_model_pr_summarisation")
        combined_comments = {
            "finetuned_comments": task_response.get("finetuned_model", {}).get("comments", []),
            "foundation_comments": task_response.get("foundation_model", {}).get("comments", []),
        }
        return combined_comments, foundation_model_pr_summarisation

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

        if model_config.get("ENABLED"):
            for _ in range(max_retry):
                try:
                    response = await client.get_client_response(
                        conversation_message, model_config.get("MODEL"), response_type
                    )
                    # IN case of PR summary, just format the code blocks if present
                    if response_type == "text":
                        pr_summary = response.content
                        return format_code_blocks(pr_summary)

                    # In case of PR review comments decode json, filter and format the comments
                    pr_review_response = json.loads(response.content)
                    if "comments" in pr_review_response:
                        filtered_comments = cls.filtered_comments(
                            pr_comments=pr_review_response,
                            confidence_filter_score=model_config.get("CONFIDENCE_SCORE"),
                        )
                        pr_comments = {"comments": filtered_comments}
                        return pr_comments

                except json.JSONDecodeError as e:
                    logger.error("JSON decode error while decoding PR review comments data: {}".format(e))
                except Exception as e:
                    logger.error("Exception occured while fetching data from openai: {}".format(e))
                await asyncio.sleep(0.2)

        return pr_summary if response_type == "text" else pr_comments

    @classmethod
    def filtered_comments(cls, pr_comments: dict, confidence_filter_score: float) -> dict:
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
        return pr_diff_token_count, relevant_chunk_token_count, pr_review_context_token_count
