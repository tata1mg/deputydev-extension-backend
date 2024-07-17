import asyncio
import json
from typing import Any, Dict, Union

from sanic.log import logger
from torpedo import CONFIG, Task

from app.common.services.openai.client import LLMClient
from app.common.utils.app_utils import (
    build_openai_conversation_message,
    get_task_response,
    get_token_count,
)
from app.common.utils.log_time import log_time
from app.main.blueprints.deputy_dev.constants import (
    MAX_PR_DIFF_TOKEN_LIMIT,
    PR_SIZE_TOO_BIG_MESSAGE,
    LLMModels,
)
from app.main.blueprints.deputy_dev.constants.prompts.v1.system_prompts import (
    SCRIT_PROMPT,
    SCRIT_SUMMARY_PROMPT,
)
from app.main.blueprints.deputy_dev.constants.prompts.v2.system_prompts import (
    SCRIT_PROMPT as SCRIT_PROMPT_V2,
)
from app.main.blueprints.deputy_dev.constants.repo import VCSTypes
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
from app.main.blueprints.deputy_dev.services.comment.comment_factory import (
    CommentFactory,
)
from app.main.blueprints.deputy_dev.services.repo.repo_factory import RepoFactory
from app.main.blueprints.deputy_dev.services.search import perform_search
from app.main.blueprints.deputy_dev.utils import (
    append_line_numbers,
    format_code_blocks,
    get_filtered_response,
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
        # Initialize repo and comment service
        vcs_type = data.get("vcs_type", VCSTypes.bitbucket.value)
        repo_name, pr_id, workspace = data.get("repo_name"), data.get("pr_id"), data.get("workspace")
        repo = await RepoFactory.repo(
            vcs_type=vcs_type,
            repo_name=repo_name,
            pr_id=pr_id,
            workspace=workspace,
        )

        comment_service = await CommentFactory.comment(
            vcs_type=vcs_type, repo_name=repo_name, pr_id=pr_id, workspace=workspace, pr_details=repo.pr_details
        )

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
            await comment_service.create_pr_comment(comment=comment, model=LLMModels.FoundationModel.value)
        else:
            is_repo_cloned, relevant_chunk = await cls.get_relevant_chunk(repo, diff)
            # if error code is 128, we successfully handle the SQS message
            if not is_repo_cloned:
                return
            response, pr_summary = await cls.parallel_pr_review_with_gpt_models(
                diff, repo.pr_details, relevant_chunk, prompt_version=data["prompt_version"]
            )
            if not response.get("finetuned_comments") and not response.get("foundation_comments"):
                # Add a "Looks Good to Me" comment to the Pull Request if no comments meet the threshold
                await comment_service.create_pr_comment("LGTM!!", LLMModels.FoundationModel.value)
            else:
                # parallel tasks to Post finetuned and foundation comments
                await comment_service.post_bots_comments(response)

            if pr_summary:
                await comment_service.create_pr_comment(pr_summary, LLMModels.FoundationModel.value)

            # Clean up by deleting the cloned repository
            repo.delete_repo()
            logger.info(f"Completed PR review for pr id - {pr_id}, repo - {data.get('repo_name')}")

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

        return pr_review_context, pr_summary_context

    @classmethod
    async def parallel_pr_review_with_gpt_models(
        cls, pr_diff: str, pr_detail: str, relevant_chunk: str, prompt_version: str
    ) -> list:
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
        pr_review_context, pr_summary_context = await cls.create_user_message(
            pr_diff_with_line_numbers, pr_detail, relevant_chunk
        )

        # using tiktoken to count the total tokens consumed by characters from relevant chunks and pr diff

        cls.log_token_counts(pr_diff_with_line_numbers, relevant_chunk, pr_review_context)

        pr_review_conversation_message = build_openai_conversation_message(
            system_message=cls.get_code_review_system_prompt(prompt_version), user_message=pr_review_context
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
        return pr_diff_token_count, relevant_chunk_token_count, pr_review_context_token_count

    @classmethod
    def get_code_review_system_prompt(cls, prompt_version: str):
        if prompt_version == "v1":
            return SCRIT_PROMPT
        elif prompt_version == "v2":
            return SCRIT_PROMPT_V2

    @classmethod
    async def get_relevant_chunk(cls, repo, diff):
        # clone the repo
        _, is_repo_cloned = await repo.clone_repo()

        # return code 128 signifies bad request to github (e.g. - If we are trying to clone a branch that does not exist in git)
        if not is_repo_cloned:
            return is_repo_cloned, None

        all_chunks, all_docs = await get_chunks(repo.repo_dir)
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
        return is_repo_cloned, relevant_chunk
