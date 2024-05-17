import asyncio
import json
import time
from typing import Any, Dict

from sanic.log import logger

from app.constants.constants import (
    CONFIDENCE_SCORE,
    MAX_LINE_CHANGES,
    PR_SIZE_TOO_BIG_MESSAGE,
    Augmentation,
)
from app.constants.repo import VCSTypes
from app.dao.repo import PullRequestResponse
from app.managers.openai_tools.openai_assistance import (
    create_review_thread,
    create_run_id,
    poll_for_success,
)
from app.modules.chunking.chunk_parsing_utils import (
    render_snippet_array,
    source_to_chunks,
)
from app.modules.repo import RepoModule
from app.modules.search import perform_search
from app.modules.tiktoken.tiktoken import TikToken
from app.utils import calculate_total_diff, get_task_response, build_openai_conversation_message
from app.modules.clients.openai.openai_client import OpenAIClient
from torpedo import Task, TaskExecutor
from torpedo import CONFIG
from typing import Any, Dict, List

finetuned_model_config = CONFIG.config.get("FINETUNED_SCRIT_MODEL")
scrit_model_config = CONFIG.config.get("SCRIT_MODEL")


class CodeReviewManager:
    """Manager for processing Pull Request reviews."""

    @classmethod
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
            branch_name=data.get("branch"),
            vcs_type=data.get("vcs_type", VCSTypes.bitbucket.value),
        )

        # Retrieve Pull Request details and diff content asynchronously
        pr_detail = await repo.get_pr_details(data.get("pr_id"))
        diff = await repo.get_pr_diff(data.get("pr_id"))

        # Trigger the background task to handle further processing
        return asyncio.ensure_future(
            cls.background_task(repo=repo, pr_id=data.get("pr_id"), pr_detail=pr_detail, diff=diff)
        )

    @classmethod
    async def background_task(cls, repo: RepoModule, pr_id: int, pr_detail: PullRequestResponse, diff: str) -> None:
        """Background task for processing Pull Request reviews.

        Args:
            repo (RepoModule): Instance of RepoModule for repository operations.
            pr_id (int): Pull Request ID.
            pr_detail (PullRequestResponse): Details of the Pull Request.
            diff (str): Diff content of the Pull Request.
            confidence_score (float): Confidence score threshold for review comments.

        Returns:
            None
        """
        # Log the start of processing
        logger.info("Processing started.")

        # Calculate the total lines of code changed in the diff content
        diff_loc = calculate_total_diff(diff)
        logger.info(f"Total diff LOC is {diff_loc}")

        # Check if diff size exceeds the maximum allowable changes
        if diff_loc > MAX_LINE_CHANGES:
            logger.info("Diff count is {}. Unable to process this request.".format(diff_loc))
            # Add a comment to the Pull Request indicating the size is too large
            comment = PR_SIZE_TOO_BIG_MESSAGE.format(diff_loc)
            await repo.create_comment_on_pr(pr_id=pr_id, comment=comment)
            return
        else:
            # Clone the repository for further processing
            repo.clone_repo()

            # Process source code into chunks and documents
            all_chunks, all_docs = source_to_chunks(repo.repo_dir)

            # Perform a search based on the diff content to find relevant chunks
            content_to_lexical_score_list = await perform_search(all_docs=all_docs, all_chunks=all_chunks, query=diff)

            # Rank relevant chunks based on lexical scores
            ranked_snippets_list = sorted(
                all_chunks,
                key=lambda chunk: content_to_lexical_score_list[chunk.denotation],
                reverse=True,
            )[:10]

            # Render relevant chunks into a single snippet
            relevant_chunk = render_snippet_array(ranked_snippets_list)
            # tiktoken_client = TikToken()
            # print('------ tokens pr diff', tiktoken_client.count(diff))
            # print('------ tokens relevant_chunk', tiktoken_client.count(diff))
            response = await cls.parallel_pr_review_with_gpt_models(diff, pr_detail, relevant_chunk)
            # Send relevant chunks and Pull Request details to an external system
            # thread = await create_review_thread(diff, pr_detail, relevant_chunk)
            # run = await create_run_id(thread)
            # response = await poll_for_success(thread, run)
            #
            if response:
                # Extract comments from the response
                comments = response.get("comments")
                logger.info("PR comments: {}".format(comments))

                if comments:
                    for comment in comments:
                        await repo.create_comment_on_pr(pr_id, comment)
                else:
                    logger.info("LGTM!")
                    # Add a "Looks Good to Me" comment to the Pull Request if no comments meet the threshold
                    await repo.create_comment_on_pr(pr_id, "LGTM!!")

            # Clean up by deleting the cloned repository
            repo.delete_repo()
            return

    @staticmethod
    def create_user_message(pr_diff: str, pr_detail: str, relevant_chunk: str) -> str:
        """
        Creates the user message for the OpenAI chat completion API.

        Args:
            pr_diff (str): The diff of the pull request.
            pr_detail (str): Details of the pull request including title and description.
            relevant_chunk (str): Relevant chunks of code for the review.

        Returns:
            str: The formatted user message.
        """
        context = (
            "You are a great code reviewer who has been given a PR to review along with some relevant chunks of code. Relevant chunks of code are enclosed within <chunk></chunk> tags. "
            f"Use the relevant chunks of code to review the PR passed. Relevant code chunks: '{relevant_chunk}, "
            f"Review this PR with Title: '{pr_detail.title}', "
            f"Description: '{pr_detail.description}', "
            f"PR_diff: {pr_diff}"
        )
        return context

    @classmethod
    async def parallel_pr_review_with_gpt_models(cls, pr_diff: str, pr_detail: str, relevant_chunk: str) -> list:
        """
        Runs a thread parallely to call normal GPT-4 and fine-tuned GPT model to review the PR and provide comments.

        Args:
            pr_diff (str): Diff of the pull request.
            pr_detail (str): Details of the pull request including title and description.
            relevant_chunk (str): Relevant chunks of code for the review.

        Returns:
            list: Combined OpenAI PR comments filtered by confidence_filter_score.
        """
        user_message = cls.create_user_message(pr_diff, pr_detail, relevant_chunk)
        conversation_message = build_openai_conversation_message(
            system_message=Augmentation.SCRIT_PROMT.value, user_message=user_message
        )
        # Create two parallel tasks to get PR reviewed by finetuned model and gpt4 model
        tasks = [
            Task(
                cls.get_openai_pr_comments(
                    conversation_message=conversation_message,
                    model=finetuned_model_config.get("MODEL"),
                    confidence_filter_score=finetuned_model_config.get("CONFIDENCE_SCORE"),
                    max_retry=2,
                ),
                result_key="finetuned_model",
            ),
            Task(
                cls.get_openai_pr_comments(
                    conversation_message=conversation_message,
                    model=scrit_model_config.get("MODEL"),
                    confidence_filter_score=scrit_model_config.get("CONFIDENCE_SCORE"),
                    max_retry=2,
                ),
                result_key="scrit_model",
            ),
        ]
        task_response = await get_task_response(tasks)
        # combine finetuned and gpt4 filtered comments
        finetuned_model_comments = task_response.get("finetuned_model")
        scrit_model_comments = task_response.get("scrit_model")
        combined_comments = {
            "comments": finetuned_model_comments.get("comments", []) + scrit_model_comments.get("comments", [])
        }
        return combined_comments

    @classmethod
    async def get_openai_pr_comments(cls, conversation_message, model, confidence_filter_score, max_retry=2):
        """
        Makes a call to OpenAI chat completion API with a specific model and conversation messages.
        Implements a retry mechanism in case of a failed request or improper response.

        Args:
            conversation_message: System and user message object.
            model: GPT model to be called.
            confidence_filter_score: Score to filter the comments.
            max_retry: Number of times OpenAI should be called in case of failure or improper response.

        Returns:
           List of filtered comment objects.
        """
        pr_comments = []
        for _ in range(max_retry):
            try:
                openai_response = await OpenAIClient().get_openai_response(conversation_message, model)
                pr_comments = json.loads(openai_response.content)
                if "comments" in pr_comments:
                    return pr_comments
                else:
                    time.sleep(0.2)
            except Exception as e:
                logger.info("Exception occured while fetching data from openai: {}".format(e))
                time.sleep(0.2)
        return cls.filtered_comments(pr_comments, confidence_filter_score)

    @staticmethod
    def filtered_comments(pr_comments: dict, confidence_filter_score: float) -> list:
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
            if float(comment.get("confidence_score")) >= float(confidence_filter_score):
                filtered_comments.append(comment)
