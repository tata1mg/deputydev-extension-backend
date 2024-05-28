import json
import time
from datetime import datetime
from typing import Any, Dict

from sanic.log import logger
from torpedo import CONFIG, Task

from app.constants.constants import (
    MAX_LINE_CHANGES,
    PR_SIZE_TOO_BIG_MESSAGE,
    Augmentation,
    LLMModels,
)
from app.constants.repo import VCSTypes
from app.modules.chunking.chunk_parsing_utils import (
    render_snippet_array,
    source_to_chunks,
)
from app.modules.clients import LLMClient
from app.modules.repo import RepoModule
from app.modules.search import perform_search
from app.utils import (
    build_openai_conversation_message,
    calculate_total_diff,
    get_task_response,
)

finetuned_model_config = CONFIG.config.get("FINETUNED_SCRIT_MODEL")
scrit_model_config = CONFIG.config.get("SCRIT_MODEL")
NO_OF_CHUNKS = CONFIG.config["CHUNKING"]["NUMBER_OF_CHUNKS"]


class CodeReviewManager:
    """Manager for processing Pull Request reviews."""

    @classmethod
    async def handle_event(cls, data: Dict[str, Any]) -> None:
        logger.info("Received SQS Message: {}".format(data))
        await cls.process_pr_review(data=data)

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
        pr_id = data.get("pr_id")
        pr_detail = await repo.get_pr_details(data.get("pr_id"))
        created_on = pr_detail.created_on
        request_time = datetime.strptime(data.get("request_time"), "%Y-%m-%dT%H:%M:%S.%f%z")
        # Calculate the time difference in minutes
        time_difference = (request_time - created_on).total_seconds() / 60
        if data.get("pr_type") == "created" and time_difference > 15:
            return logger.info(f"PR - {pr_id} for repo - {data.get('repo_name')} is not in creation state")
        else:
            diff = await repo.get_pr_diff(data.get("pr_id"))
            if diff == "":
                return logger.info(
                    f"PR - {pr_id} for repo - {data.get('repo_name')} doesn't contain any valid files to review"
                )
            # Calculate the total lines of code changed in the diff content
            diff_loc = calculate_total_diff(diff)
            logger.info(f"Total diff LOC is {diff_loc}")

            # Check if diff size exceeds the maximum allowable changes
            if diff_loc > MAX_LINE_CHANGES:
                logger.info("Diff count is {}. Unable to process this request.".format(diff_loc))
                # Add a comment to the Pull Request indicating the size is too large
                comment = PR_SIZE_TOO_BIG_MESSAGE.format(diff_loc)
                await repo.create_comment_on_pr(pr_id=pr_id, comment=comment, model=LLMModels.FoundationModel.value)
                return
            else:
                # Clone the repository for further processing
                await repo.clone_repo()

                # Process source code into chunks and documents
                all_chunks, all_docs = source_to_chunks(repo.repo_dir)
                logger.info("Completed chunk creation")

                # Perform a search based on the diff content to find relevant chunks
                content_to_lexical_score_list = await perform_search(
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

                response, pr_summary = await cls.parallel_pr_review_with_gpt_models(diff, pr_detail, relevant_chunk)
                if not response.get("finetuned_comments") and not response.get("foundation_comments"):
                    # Add a "Looks Good to Me" comment to the Pull Request if no comments meet the threshold
                    await repo.create_comment_on_pr(pr_id, "LGTM!!", LLMModels.FoundationModel.value)
                else:
                    # parallel tasks to Post finetuned and foundation comments
                    await repo.post_bots_comments(response, pr_id)

                if pr_summary:
                    await repo.create_comment_on_pr(pr_id, pr_summary, LLMModels.FoundationModel.value)

                logger.info(f"Completed PR review for {data.get('repo_name')}, PR - {pr_id}")
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

        user_story_description = """
        Old logic:
            We release redis lock on order key and booking id only for cancelled orders 
        New logic:
            We want to release redis lock on order key and booking id for both cancelled and delivered orders.
            Please ensure that this change shouldn't impact any other flow.
       """

        pr_review_context = (
            "You are a great code reviewer who has been given a PR to review along with some relevant chunks of code. Relevant chunks of code are enclosed within <relevant_chunks_in_repo></relevant_chunks_in_repo> tags. "
            f"Following is the user story description - {user_story_description}. You should use this to make comments around change in business logic that is not expected to do."
            f"Use the relevant chunks of code to review the PR passed. Relevant code chunks: '{relevant_chunk}, "
            f"Review this PR with Title: '{pr_detail.title}', "
            f"Description: '{pr_detail.description}', "
            f"PR_diff: {pr_diff}"
        )

        pr_summary_context = f"What does the following PR do ? PR diff: {pr_diff}"

        return pr_review_context, pr_summary_context

    @classmethod
    async def parallel_pr_review_with_gpt_models(cls, pr_diff: str, pr_detail: str, relevant_chunk: str) -> tuple:
        """
        Runs a thread parallely to call normal GPT-4 and fine-tuned GPT model to review the PR and provide comments.

        Args:
            pr_diff (str): Diff of the pull request.
            pr_detail (str): Details of the pull request including title and description.
            relevant_chunk (str): Relevant chunks of code for the review.

        Returns:
            Tuple[Dict, str]: Combined OpenAI PR comments filtered by confidence_filter_score and PR summary.
        """
        pr_review_context, pr_summary_context = cls.create_user_message(pr_diff, pr_detail, relevant_chunk)
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
                    model=finetuned_model_config.get("MODEL"),
                    client_type="openai",
                    confidence_filter_score=finetuned_model_config.get("CONFIDENCE_SCORE"),
                    max_retry=2,
                ),
                result_key="finetuned_model",
            ),
            # PR review by scrit model
            Task(
                cls.get_client_pr_comments(
                    conversation_message=pr_review_conversation_message,
                    model=scrit_model_config.get("MODEL"),
                    confidence_filter_score=scrit_model_config.get("CONFIDENCE_SCORE"),
                    max_retry=2,
                    client_type="openai",
                ),
                result_key="foundation_model",
            ),
            # PR summarisation by scrit model
            Task(
                cls.get_client_pr_comments(
                    conversation_message=pr_review_summarisation_converstation_message,
                    model=scrit_model_config.get("MODEL"),
                    confidence_filter_score=scrit_model_config.get("CONFIDENCE_SCORE"),
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
            "finetuned_comments": task_response.get("finetuned_model").get("comments", []),
            "foundation_comments": task_response.get("foundation_model").get("comments", []),
        }
        return combined_comments, foundation_model_pr_summarisation

    @classmethod
    async def get_client_pr_comments(
        cls, conversation_message, model, client_type, confidence_filter_score, response_type="json_object", max_retry=2
    ):
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
        client = LLMClient(client_type=client_type)
        pr_comments = []
        pr_summary = ""
        for _ in range(max_retry):
            try:
                response = await client.get_client_response(conversation_message, model, response_type)
                if response_type == "text":
                    pr_summary = response.content
                    return pr_summary
                pr_comments = json.loads(response.content)
                if "comments" in pr_comments:
                    return pr_comments
                else:
                    time.sleep(0.2)
            except Exception as e:
                logger.error("Exception occured while fetching data from openai: {}".format(e))
                time.sleep(0.2)
        if response_type == "text":
            return pr_summary
        else:
            return cls.filtered_comments(pr_comments, client, confidence_filter_score), pr_summary

    @staticmethod
    def filtered_comments(pr_comments: dict, client: LLMClient, confidence_filter_score: float) -> list:
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
            if client.get_filtered_response(comment, confidence_filter_score):
                filtered_comments.append(comment)
        return filtered_comments
