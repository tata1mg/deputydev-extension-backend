from datetime import datetime
from typing import Any, Dict

from pydantic import ValidationError
from sanic.log import logger
from torpedo import CONFIG

from app.common.utils.log_time import log_time
from app.main.blueprints.deputy_dev.constants.constants import (
    PR_SIZE_TOO_BIG_MESSAGE,
    PrStatusTypes,
)
from app.main.blueprints.deputy_dev.constants.repo import VCSTypes
from app.main.blueprints.deputy_dev.loggers import AppLogger
from app.main.blueprints.deputy_dev.models.code_review_request import CodeReviewRequest
from app.main.blueprints.deputy_dev.services.code_review.multi_agent_pr_review_manager import (
    MultiAgentPRReviewManager,
)
from app.main.blueprints.deputy_dev.services.code_review.post_processors.pr_review_post_processor import (
    PRReviewPostProcessor,
)
from app.main.blueprints.deputy_dev.services.code_review.pre_processors.pr_review_pre_processor import (
    PRReviewPreProcessor,
)
from app.main.blueprints.deputy_dev.services.code_review.single_agent_pr_review_manager import (
    SingleAgentPRReviewManager,
)
from app.main.blueprints.deputy_dev.services.comment.affirmation_comment_service import (
    AffirmationService,
)
from app.main.blueprints.deputy_dev.services.comment.base_comment import BaseComment
from app.main.blueprints.deputy_dev.services.comment.comment_factory import (
    CommentFactory,
)
from app.main.blueprints.deputy_dev.services.context_var import identifier
from app.main.blueprints.deputy_dev.services.pr.pr_service import PRService
from app.main.blueprints.deputy_dev.services.repo.base_repo import BaseRepo
from app.main.blueprints.deputy_dev.services.repo.repo_factory import RepoFactory
from app.main.blueprints.deputy_dev.services.workspace.context_vars import (
    get_context_value,
    set_context_values,
)
from app.main.blueprints.deputy_dev.utils import get_vcs_auth_handler

NO_OF_CHUNKS = CONFIG.config["CHUNKING"]["NUMBER_OF_CHUNKS"]
config = CONFIG.config


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
            AppLogger.log_info("Completed PR review: ")
        except ValidationError as e:
            AppLogger.log_error(f"Received Invalid SQS Message - {data}: {e}")
        except Exception as e:
            AppLogger.log_error(f"Unable to review PR: {e}")
            raise

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
        affirmation_service = AffirmationService(data, comment_service)
        pr_dto = None

        try:
            tokens_data, execution_start_time = None, datetime.now()
            is_reviewable_request, pr_dto = await PRReviewPreProcessor(
                repo_service, comment_service, affirmation_service
            ).pre_process_pr()
            if not is_reviewable_request:
                return
            llm_comments, tokens_data, meta_info_to_save, is_large_pr = await cls.review_pr(
                repo_service, comment_service, data["prompt_version"]
            )
            meta_info_to_save["execution_start_time"] = execution_start_time
            await PRReviewPostProcessor(repo_service, comment_service, affirmation_service).post_process_pr(
                pr_dto, llm_comments, tokens_data, is_large_pr, meta_info_to_save
            )

        except Exception as ex:
            # if PR is inserted in db then only we will update status
            if pr_dto:
                await PRService.db_update(
                    payload={
                        "review_status": PrStatusTypes.FAILED.value,
                    },
                    filters={"id": pr_dto.id},
                )
            raise ex
        finally:
            repo_service.delete_repo()

    @classmethod
    def meta_info_to_save(cls):
        return {"issue_id": "OS-1718", "confluence_doc_id": None}

    @classmethod
    def llm_comments(cls):
        return [
            {
                "file_path": "app/modules/pharma_pdp/utils/utility.py",
                "line_number": "712",
                "comment": "Critical: The function 'error_function' contains a deliberate division by zero error, which will cause a runtime exception and crash the program. This is a severe logical error that needs to be addressed immediately.",
                "buckets": [{"name": "ERROR", "agent_id": "255c5d79-b3ce-4b0b-aa6d-f96096aa6a2f"}],
                "corrective_code": 'def error_function(cls):\n    # Remove the division by zero\n    # Add appropriate error handling or logic here\n    return "Function executed successfully"',
                "confidence_score": 1.0,
                "model": "CLAUDE_3_POINT_5_SONNET",
                "is_valid": None,
                "scm_comment_id": 582203559,
            },
            {
                "file_path": "app/modules/pharma_pdp/utils/utility.py",
                "line_number": "713",
                "comment": "High: The function 'error_function' contains unreachable code after the division by zero error. This is a logical error as the second line will never be executed due to the exception raised by the first line.",
                "buckets": [{"name": "ERROR", "agent_id": "255c5d79-b3ce-4b0b-aa6d-f96096aa6a2f"}],
                "corrective_code": 'def error_function(cls):\n    # Remove both lines and implement proper functionality\n    return "Function executed successfully"',
                "confidence_score": 1.0,
                "model": "CLAUDE_3_POINT_5_SONNET",
                "is_valid": None,
                "scm_comment_id": 582203563,
            },
            {
                "file_path": "app/modules/pharma_pdp/utils/utility.py",
                "line_number": "711",
                "comment": "Medium: The 'error_function' is defined as an instance method (using 'cls' parameter) but it doesn't use any class or instance attributes. This is a semantic error that could lead to confusion and potential bugs in the future.",
                "buckets": [{"name": "ERROR", "agent_id": "255c5d79-b3ce-4b0b-aa6d-f96096aa6a2f"}],
                "corrective_code": '@staticmethod\ndef error_function():\n    # Implement proper functionality here\n    return "Function executed successfully"',
                "confidence_score": 0.9,
                "model": "CLAUDE_3_POINT_5_SONNET",
                "is_valid": None,
                "scm_comment_id": 582203565,
            },
        ]

    @classmethod
    def tokens(cls):
        return {
            "error_agentPASS_1": {
                "pr_title": 6,
                "pr_description": 0,
                "pr_diff_tokens": 2047,
                "relevant_chunk": 2043,
                "system_prompt": 51,
                "user_prompt": 9190,
                "input_tokens": 11895,
                "output_tokens": 546,
            }
        }

    @classmethod
    def check_no_pr_comments(cls, llm_response):
        return not llm_response

    @classmethod
    async def review_pr(cls, repo_service: BaseRepo, comment_service: BaseComment, prompt_version):
        is_agentic_review_enabled = CONFIG.config["PR_REVIEW_SETTINGS"]["MULTI_AGENT_ENABLED"]
        _review_klass = MultiAgentPRReviewManager if is_agentic_review_enabled else SingleAgentPRReviewManager
        # llm_response, pr_summary, tokens_data, meta_info_to_save, _is_large_pr = await _review_klass(
        #     repo_service, prompt_version
        # ).get_code_review_comments()
        llm_response, pr_summary, tokens_data, meta_info_to_save, _is_large_pr = (
            cls.llm_comments(),
            "",
            cls.tokens(),
            cls.meta_info_to_save(),
            False,
        )
        # We will only post summary for forst PR review request
        if pr_summary and not get_context_value("has_reviewed_entry"):
            await repo_service.update_pr_description(pr_summary.get("response"))

        if _is_large_pr:
            await comment_service.create_pr_comment(
                comment=PR_SIZE_TOO_BIG_MESSAGE, model=config.get("FEATURE_MODELS").get("PR_REVIEW")
            )
        elif cls.check_no_pr_comments(llm_response):
            await comment_service.create_pr_comment("LGTM!!", config.get("FEATURE_MODELS").get("PR_REVIEW"))
        else:
            await comment_service.post_bots_comments(llm_response)
        return llm_response, tokens_data, meta_info_to_save, _is_large_pr

    @classmethod
    async def initialise_services(cls, data: dict):
        cls.set_identifier(data.get("repo_name"))  # need to deprecate
        set_context_values(scm_pr_id=data.get("pr_id"), repo_name=data.get("repo_name"))

        vcs_type = data.get("vcs_type", VCSTypes.bitbucket.value)
        repo_name, pr_id, workspace, scm_workspace_id, repo_id, workspace_slug = (
            data.get("repo_name"),
            data.get("pr_id"),
            data.get("workspace"),
            data.get("workspace_id"),
            data.get("repo_id"),
            data.get("workspace_slug"),
        )
        auth_handler = await get_vcs_auth_handler(scm_workspace_id, vcs_type)
        repo_service = await RepoFactory.repo(
            vcs_type=vcs_type,
            repo_name=repo_name,
            pr_id=pr_id,
            workspace=workspace,
            workspace_id=scm_workspace_id,
            workspace_slug=workspace_slug,
            auth_handler=auth_handler,
            repo_id=repo_id,
            fetch_pr_details=True,
        )
        comment_service = await CommentFactory.initialize(
            vcs_type=vcs_type,
            repo_name=repo_name,
            pr_id=pr_id,
            workspace=workspace,
            workspace_slug=workspace_slug,
            pr_details=repo_service.pr_details,
            auth_handler=auth_handler,
            repo_id=repo_id,
        )
        return repo_service, comment_service
