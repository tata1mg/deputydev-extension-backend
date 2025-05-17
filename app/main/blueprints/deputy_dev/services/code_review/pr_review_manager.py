from datetime import datetime
from typing import Any, Dict

from deputydev_core.services.initialization.review_initialization_manager import ReviewInitialisationManager
from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.context_vars import set_context_values
from pydantic import ValidationError
from sanic.log import logger
from torpedo import CONFIG

from app.backend_common.services.pr.base_pr import BasePR
from app.backend_common.services.repo.base_repo import BaseRepo
from app.backend_common.services.workspace.context_var import identifier
from app.backend_common.utils.log_time import log_time
from app.main.blueprints.deputy_dev.constants.constants import (
    PR_SIZE_TOO_BIG_MESSAGE,
    PrStatusTypes,
)
from app.main.blueprints.deputy_dev.helpers.pr_diff_handler import PRDiffHandler
from app.main.blueprints.deputy_dev.models.code_review_request import CodeReviewRequest
from app.main.blueprints.deputy_dev.services.code_review.base_pr_review_manager import (
    BasePRReviewManager,
)
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
from app.main.blueprints.deputy_dev.services.repository.pr.pr_service import PRService
from deputydev_core.utils.weaviate import clean_weaviate_collections

NO_OF_CHUNKS = CONFIG.config["CHUNKING"]["NUMBER_OF_CHUNKS"]
config = CONFIG.config


class PRReviewManager(BasePRReviewManager):
    """Manager for processing Pull Request reviews."""

    @classmethod
    async def handle_event(cls, data: Dict[str, Any]) -> None:
        # Although we will be receiving validated payload, this is just an edge case handling, where
        # someone was able to manually push invalid message to SQS, we will check the incoming SQS message
        # if it's fine then we start the PR review process, otherwise we log the invalid payload and purge the message
        try:
            CodeReviewRequest(**data)
            logger.info("Received MessageQueue Message: {}".format(data))
            await cls.process_pr_review(data=data)
            AppLogger.log_info("Completed PR review: ")
        except ValidationError as e:
            AppLogger.log_error(f"Received Invalid Message From MessageQueue - {data}: {e}")
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
        repo_service, pr_service, comment_service = await cls.initialise_services(data)
        pr_diff_handler = PRDiffHandler(pr_service)
        affirmation_service = AffirmationService(data, comment_service)
        pre_processor = None

        try:
            tokens_data, execution_start_time = None, datetime.now()
            pre_processor = PRReviewPreProcessor(
                repo_service=repo_service,
                pr_service=pr_service,
                comment_service=comment_service,
                affirmation_service=affirmation_service,
                pr_diff_handler=pr_diff_handler,
            )
            await pre_processor.pre_process_pr()

            if not pre_processor.is_reviewable_request:
                return
            set_context_values(session_id=pre_processor.session_id)
            if not pre_processor.session_id:
                AppLogger.log_error("Session id not found for PR review")
                raise Exception("Session id not found for PR review")

            llm_comments, tokens_data, meta_info_to_save, is_large_pr = await cls.review_pr(
                pre_processor.session_id,
                repo_service,
                comment_service,
                pr_service,
                data["prompt_version"],
                pr_diff_handler,
            )
            meta_info_to_save["execution_start_time"] = execution_start_time
            meta_info_to_save["pr_review_start_time"] = data.get("pr_review_start_time")
            await PRReviewPostProcessor(
                pr_service=pr_service,
                comment_service=comment_service,
                affirmation_service=affirmation_service,
            ).post_process_pr(pre_processor.pr_dto, llm_comments, tokens_data, is_large_pr, meta_info_to_save)

        except Exception as ex:
            # if PR is inserted in db then only we will update status
            if pre_processor and pre_processor.pr_dto:
                await PRService.db_update(
                    payload={
                        "review_status": PrStatusTypes.FAILED.value,
                    },
                    filters={"id": pre_processor.pr_dto.id},
                )
            AppLogger.log_error("Error while processing PR review")
            raise ex
        finally:
            repo_service.delete_local_repo()
            initialisation_manager = ReviewInitialisationManager()
            await clean_weaviate_collections(initialisation_manager)

    @classmethod
    def check_no_pr_comments(cls, llm_response):
        return not llm_response

    @classmethod
    async def review_pr(
        cls,
        session_id: int,
        repo_service: BaseRepo,
        comment_service: BaseComment,
        pr_service: BasePR,
        prompt_version,
        pr_diff_handler: PRDiffHandler,
    ):
        is_agentic_review_enabled = CONFIG.config["PR_REVIEW_SETTINGS"]["MULTI_AGENT_ENABLED"]
        _review_klass = MultiAgentPRReviewManager if is_agentic_review_enabled else SingleAgentPRReviewManager
        llm_response, pr_summary, tokens_data, meta_info_to_save, _is_large_pr = await _review_klass(
            repo_service, pr_service, pr_diff_handler, session_id, prompt_version
        ).get_code_review_comments()

        # We will only post summary for first PR review request
        if pr_summary:
            await pr_service.update_pr_description(pr_summary)

        if _is_large_pr:
            await comment_service.create_pr_comment(
                comment=PR_SIZE_TOO_BIG_MESSAGE, model=config.get("FEATURE_MODELS").get("PR_REVIEW")
            )
        elif cls.check_no_pr_comments(llm_response):
            await comment_service.create_pr_comment("LGTM!!", config.get("FEATURE_MODELS").get("PR_REVIEW"))
        else:
            await comment_service.post_bots_comments(llm_response)

        return llm_response, tokens_data, meta_info_to_save, _is_large_pr
