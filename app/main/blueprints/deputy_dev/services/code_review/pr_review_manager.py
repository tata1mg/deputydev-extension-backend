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
            # llm_comments, tokens_data, meta_info_to_save, is_large_pr = (
            #     cls.llm_comments_v2(),
            #     cls.tokens(),
            #     cls.meta_info_to_save(),
            #     False,
            # )
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
    def llm_comments(cls):
        return [
            {
                "file_path": "app/modules/pharma_pdp/services/cacha_managers/interacting_brands_by_drug_id_cache_manager.py",
                "line_number": "12",
                "comment": "The `InteractingBrandsByDrugIdCacheManager` class has been updated with caching functionality, but there's no error handling or fallback mechanism implemented. This could lead to potential issues if the cache or the content service fails.",
                "buckets": ["CODE_ROBUSTNESS"],
                "agent_ids": ["ccfe1b06-f5f2-42b1-a209-4d560edbd5f4"],
                "corrective_code": 'async def interacting_drugs_data(cls, cache_key_data, headers):\n    drug_id = cache_key_data["drug_id"]\n    if is_blank(drug_id):\n        return None\n\n    try:\n        interacting_drugs = await ContentServiceClient.drug_interaction_by_drug_id(drug_id)\n    except Exception as e:\n        logger.error(f"Error fetching drug interaction data: {str(e)}")\n        return None  # Consider returning a default or cached value here\n\n    if is_blank(interacting_drugs):\n        return None\n\n    interacting_drug_hash = {}\n    # Process the interacting drugs data...\n\n    return interacting_drug_hash',
                "confidence_score": 0.9,
                "model": "CLAUDE_3_POINT_5_SONNET",
                "is_valid": True,
                "scm_comment_id": 581083728,
            },
            {
                "file_path": "app/modules/pharma_pdp/utils/utility.py",
                "line_number": "711",
                "comment": "- **MAINTAINABILITY**: The `is_tata_neu_affiliate` method is duplicated in the Utils class. This violates the DRY (Don't Repeat Yourself) principle and can lead to confusion and maintenance issues.",
                "corrective_code": '# Remove the duplicate method:\n# @staticmethod\n# def is_tata_neu_affiliate(user_context) -> bool:\n#     """Checks if user is tata neu affiliated\n# \n#     Args:\n#         user_context (UserContext): user context in headers\n# \n#     Returns:\n#         bool: True if user is affiliated to tata neu\n#     """\n#     return user_context.affiliate_source == "tcp"\n\n# Keep only one instance of the method',
                "confidence_score": 0.95,
                "buckets": ["MAINTAINABILITY"],
                "agent_ids": ["ccfe1b06-f5f2-42b1-a209-4d560edbd5f4", "4a3f593d-73cd-41d6-85a0-dc96c17ce9bb"],
                "model": "CLAUDE_3_POINT_5_SONNET",
                "agent": None,
                "is_valid": True,
                "is_summarized": True,
                "scm_comment_id": 581083734,
            },
        ]

    @classmethod
    def llm_comments_v2(cls):
        return [
            {
                "file_path": "app/modules/pharma_pdp/services/sku/drug/drug_static_service.py",
                "line_number": "166",
                "comment": "The `DrugStaticService` now uses `child_drug_id` instead of `drug_id` for fetching medicine interactions. This change might have implications for other parts of the system. Consider adding a comment explaining the reason for this change and its potential impact.",
                "buckets": [{"name": "CODE_QUALITY", "agent_id": "ccfe1b06-f5f2-42b1-a209-4d560edbd5f4"}],
                "confidence_score": 0.9,
                "corrective_code": "\nasync def medicine_interaction(self):\n    if self.sku.child_drug_id:\n        try:\n            # Using child_drug_id instead of drug_id for more specific interaction data\n            # Note: This change may affect other parts of the system that rely on drug_id\n            # TODO: Update related components to use child_drug_id where appropriate\n            return await InteractingBrandsByDrugIdCacheManager.interacting_drugs(\n                self.sku.child_drug_id, self.headers\n            )\n        except BaseSanicException:\n            pass\n    return None\n",
                "model": "CLAUDE_3_POINT_5_SONNET",
                "is_valid": None,
                "scm_comment_id": 581102197,
            },
            {
                "file_path": "app/modules/pharma_pdp/utils/utility.py",
                "line_number": "711",
                "comment": "The utility method `is_tata_neu_affiliate` has been added, but it appears to be a duplicate of an existing method. Remove the duplicate method to avoid confusion and maintain a single source of truth.",
                "buckets": [{"name": "CODE_QUALITY", "agent_id": "ccfe1b06-f5f2-42b1-a209-4d560edbd5f4"}],
                "confidence_score": 0.95,
                "corrective_code": '\n# Remove the following duplicate method:\n# @staticmethod\n# def is_tata_neu_affiliate(user_context) -> bool:\n#     """Checks if user is tata neu affiliated\n#\n#     Args:\n#         user_context (UserContext): user context in headers\n#\n#     Returns:\n#         bool: True if user is affiliated to tata neu\n#     """\n#     return user_context.affiliate_source == "tcp"\n\n# Keep only the original method\n',
                "model": "CLAUDE_3_POINT_5_SONNET",
                "is_valid": None,
                "scm_comment_id": 581102198,
            },
            {
                "file_path": "app/modules/pharma_pdp/utils/utility.py",
                "line_number": "+711",
                "comment": "The `is_tata_neu_affiliate` method in the `Utils` class appears to be duplicated. This could lead to confusion and maintenance issues in the future.",
                "buckets": [{"name": "ERROR", "agent_id": "4a3f593d-73cd-41d6-85a0-dc96c17ce9bb"}],
                "confidence_score": 0.95,
                "corrective_code": '\n# Remove the duplicate method and keep only one instance of is_tata_neu_affiliate\nclass Utils:\n    # ... other methods ...\n\n    @staticmethod\n    def is_tata_neu_affiliate(user_context) -> bool:\n        """Checks if user is tata neu affiliated\n\n        Args:\n            user_context (UserContext): user context in headers\n\n        Returns:\n            bool: True if user is affiliated to tata neu\n        """\n        return user_context.affiliate_source == "tcp"\n\n    # Remove the duplicate method\n',
                "model": "CLAUDE_3_POINT_5_SONNET",
                "is_valid": None,
                "scm_comment_id": 581102199,
            },
        ]

    @classmethod
    def tokens(cls):
        return {
            "securityPASS_1": {
                "pr_title": 6,
                "pr_description": 3901,
                "pr_diff_tokens": 16693,
                "system_prompt": 69,
                "user_prompt": 26133,
                "input_tokens": 30998,
                "output_tokens": 1025,
            },
            "performance_optimisationPASS_1": {
                "pr_title": 6,
                "pr_description": 3901,
                "pr_diff_tokens": 16693,
                "relevant_chunk": 5390,
                "system_prompt": 90,
                "user_prompt": 30206,
                "input_tokens": 31091,
                "output_tokens": 960,
            },
            "code_communicationPASS_1": {
                "pr_title": 6,
                "pr_description": 3901,
                "pr_diff_tokens": 16693,
                "relevant_chunk": 5390,
                "pr_user_story": 0,
                "pr_confluence": None,
                "system_prompt": 89,
                "user_prompt": 26195,
                "input_tokens": 35920,
                "output_tokens": 540,
            },
            "code_maintainabilityPASS_1": {
                "pr_title": 6,
                "pr_description": 3901,
                "pr_diff_tokens": 16693,
                "relevant_chunk": 5390,
                "system_prompt": 104,
                "user_prompt": 30510,
                "input_tokens": 36291,
                "output_tokens": 1497,
            },
            "errorPASS_1": {
                "pr_title": 6,
                "pr_description": 3901,
                "pr_diff_tokens": 16693,
                "relevant_chunk": 5390,
                "system_prompt": 78,
                "user_prompt": 30176,
                "input_tokens": 35905,
                "output_tokens": 284,
            },
            "pr_summaryPASS_1": {
                "pr_title": 6,
                "pr_description": 3901,
                "pr_diff_tokens": 16693,
                "system_prompt": 110,
                "user_prompt": 16711,
                "input_tokens": 16832,
                "output_tokens": 387,
            },
            "securityPASS_2": {
                "pr_title": 6,
                "pr_description": 3901,
                "pr_diff_tokens": 16693,
                "system_prompt": 69,
                "user_prompt": 26263,
                "input_tokens": 31132,
                "output_tokens": 349,
            },
            "performance_optimisationPASS_2": {
                "pr_title": 6,
                "pr_description": 3901,
                "pr_diff_tokens": 16693,
                "relevant_chunk": 5390,
                "system_prompt": 84,
                "user_prompt": 30265,
                "input_tokens": 31360,
                "output_tokens": 1213,
            },
            "code_communicationPASS_2": {
                "pr_title": 6,
                "pr_description": 3901,
                "pr_diff_tokens": 16693,
                "relevant_chunk": 5390,
                "pr_user_story": 0,
                "pr_confluence": None,
                "system_prompt": 78,
                "user_prompt": 26469,
                "input_tokens": 35972,
                "output_tokens": 810,
            },
            "code_maintainabilityPASS_2": {
                "pr_title": 6,
                "pr_description": 3901,
                "pr_diff_tokens": 16693,
                "relevant_chunk": 5390,
                "system_prompt": 126,
                "user_prompt": 30653,
                "input_tokens": 36492,
                "output_tokens": 1209,
            },
            "errorPASS_2": {
                "pr_title": 6,
                "pr_description": 3901,
                "pr_diff_tokens": 16693,
                "relevant_chunk": 5390,
                "system_prompt": 99,
                "user_prompt": 30449,
                "input_tokens": 36192,
                "output_tokens": 414,
            },
        }

    @classmethod
    def meta_info_to_save(cls):
        import datetime

        return {
            "issue_id": "OS-1518",
            "confluence_doc_id": None,
            "execution_start_time": datetime.datetime(2024, 12, 23, 20, 24, 46, 606084),
        }

    @classmethod
    def check_no_pr_comments(cls, llm_response):
        return not llm_response

    @classmethod
    async def review_pr(cls, repo_service: BaseRepo, comment_service: BaseComment, prompt_version):
        is_agentic_review_enabled = CONFIG.config["PR_REVIEW_SETTINGS"]["MULTI_AGENT_ENABLED"]
        _review_klass = MultiAgentPRReviewManager if is_agentic_review_enabled else SingleAgentPRReviewManager
        llm_response, pr_summary, tokens_data, meta_info_to_save, _is_large_pr = await _review_klass(
            repo_service, prompt_version
        ).get_code_review_comments()

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
