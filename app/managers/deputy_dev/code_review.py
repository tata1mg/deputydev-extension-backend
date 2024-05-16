import asyncio
from typing import Any, Dict

from sanic.log import logger

from app.constants.constants import (
    CONFIDENCE_SCORE,
    MAX_LINE_CHANGES,
    PR_SIZE_TOO_BIG_MESSAGE,
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
from app.utils import calculate_total_diff


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

        # Set confidence score threshold, defaulting to a predefined value if not provided
        confidence_score = data.get("confidence_score", CONFIDENCE_SCORE)

        # Trigger the background task to handle further processing
        return asyncio.ensure_future(
            cls.background_task(
                repo=repo, pr_id=data.get("pr_id"), pr_detail=pr_detail, diff=diff, confidence_score=confidence_score
            )
        )

    @staticmethod
    async def background_task(
        repo: RepoModule, pr_id: int, pr_detail: PullRequestResponse, diff: str, confidence_score: float
    ) -> None:
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

            # Send relevant chunks and Pull Request details to an external system
            thread = await create_review_thread(diff, pr_detail, relevant_chunk)
            run = await create_run_id(thread)
            response = await poll_for_success(thread, run)

            if response:
                # Extract comments from the response
                comments = response.get("comments")
                logger.info("PR comments: {}".format(comments))

                # Check if any comment meets the confidence score threshold
                if any(float(comment.get("confidence_score")) >= float(confidence_score) for comment in comments):
                    for comment in comments:
                        if float(comment.get("confidence_score")) >= float(confidence_score):
                            # Add comments meeting the threshold to the Pull Request
                            await repo.create_comment_on_pr(pr_id, comment)
                else:
                    logger.info("LGTM!")
                    # Add a "Looks Good to Me" comment to the Pull Request if no comments meet the threshold
                    await repo.create_comment_on_pr(pr_id, "LGTM!!")

            # Clean up by deleting the cloned repository
            repo.delete_repo()
            return
