from datetime import datetime
from typing import Any, Dict

from pydantic import ValidationError
from sanic.log import logger
from torpedo import CONFIG

from app.common.utils.log_time import log_time
from app.main.blueprints.deputy_dev.constants import PRReviewExperimentSet
from app.main.blueprints.deputy_dev.constants.constants import PrStatusTypes
from app.main.blueprints.deputy_dev.constants.repo import VCSTypes
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
from app.main.blueprints.deputy_dev.services.comment.base_comment import BaseComment
from app.main.blueprints.deputy_dev.services.comment.comment_factory import (
    CommentFactory,
)
from app.main.blueprints.deputy_dev.services.context_var import identifier
from app.main.blueprints.deputy_dev.services.pr.pr_service import PRService
from app.main.blueprints.deputy_dev.services.repo.base_repo import BaseRepo
from app.main.blueprints.deputy_dev.services.repo.repo_factory import RepoFactory

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
            logger.info(
                f"PR review failed for pr - {repo_service.pr_id}, repo_name - {data.get('repo_name')} "
                f"exception {ex}"
            )
            raise ex
        finally:
            repo_service.delete_repo()

    @classmethod
    def check_no_pr_comments(cls, llm_response):
        if not llm_response:
            return True
        return not any(agent_response.get("comments") for agent_response in llm_response.values())

    @classmethod
    async def review_pr(cls, repo_service: BaseRepo, comment_service: BaseComment, prompt_version):
        is_agentic_review_enabled = CONFIG.config["PR_REVIEW_SETTINGS"]["MULTI_AGENT_ENABLED"]
        _review_klass = MultiAgentPRReviewManager if is_agentic_review_enabled else SingleAgentPRReviewManager

        llm_response, pr_summary, tokens_data, meta_info_to_save = await _review_klass(
            repo_service, prompt_version
        ).get_code_review_comments()

        if pr_summary:
            await repo_service.update_pr_description(pr_summary.get("response"))

        if cls.check_no_pr_comments(llm_response):
            await comment_service.create_pr_comment("LGTM!!", config.get("FEATURE_MODELS").get("PR_REVIEW"))
        else:
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
