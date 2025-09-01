from typing import Any, Dict, Optional

from deputydev_core.utils.app_logger import AppLogger
from deputydev_core.utils.constants.enums import Clients, ContextValueKeys
from deputydev_core.utils.context_value import ContextValue
from deputydev_core.utils.context_vars import get_context_value, set_context_values

from app.backend_common.constants.constants import LARGE_PR_DIFF, PR_NOT_FOUND, PRStatus
from app.backend_common.models.dto.message_sessions_dto import MessageSessionData
from app.backend_common.models.dto.repo_dto import RepoDTO
from app.backend_common.models.dto.user_team_dto import UserTeamDTO
from app.backend_common.models.dto.workspace_dto import WorkspaceDTO
from app.backend_common.repository.message_sessions.repository import (
    MessageSessionsRepository,
)
from app.backend_common.repository.repo.repository import RepoRepository
from app.backend_common.repository.user_teams.user_team_repository import (
    UserTeamRepository,
)
from app.backend_common.services.pr.base_pr import BasePR
from app.backend_common.services.repo.base_repo import BaseRepo
from app.backend_common.services.workspace.workspace_service import WorkspaceService
from app.backend_common.utils.app_utils import get_token_count
from app.backend_common.utils.sanic_wrapper import CONFIG
from app.main.blueprints.deputy_dev.client.one_dev_review_client import (
    OneDevReviewClient,
)
from app.main.blueprints.deputy_dev.constants.constants import (
    MAX_PR_DIFF_TOKEN_LIMIT,
    PR_SIZE_TOO_BIG_MESSAGE,
    ExperimentStatusTypes,
    FeatureFlows,
    PRReviewExperimentSet,
    PrStatusTypes,
)
from app.main.blueprints.deputy_dev.helpers.pr_diff_handler import PRDiffHandler
from app.main.blueprints.deputy_dev.models.dto.pr_dto import PullRequestDTO
from app.main.blueprints.deputy_dev.services.comment.affirmation_comment_service import (
    AffirmationService,
)
from app.main.blueprints.deputy_dev.services.comment.base_comment import BaseComment
from app.main.blueprints.deputy_dev.services.experiment.experiment_service import (
    ExperimentService,
)
from app.main.blueprints.deputy_dev.services.repository.pr.pr_service import PRService
from app.main.blueprints.deputy_dev.services.setting.setting_service import (
    SettingService,
)

config = CONFIG.config
one_dev_review_client = OneDevReviewClient()


class PRReviewPreProcessor:
    def __init__(
        self,
        repo_service: BaseRepo,
        pr_service: BasePR,
        comment_service: BaseComment,
        affirmation_service: AffirmationService,
        pr_diff_handler: PRDiffHandler,
    ) -> None:
        self.repo_service = repo_service
        self.pr_service = pr_service
        self.comment_service = comment_service
        self.pr_model = pr_service.pr_model()
        self.experiment_set = None
        self.is_valid = True
        self.review_status = PrStatusTypes.IN_PROGRESS.value
        self.tokens_info = {}
        self.meta_info = {}
        self.pr_dto = None
        self.pr_diff_token_count = None
        self.affirmation_service = affirmation_service
        self.completed_pr_count = 0
        self.loc_changed = 0
        self.pr_diff_handler = pr_diff_handler
        self.is_reviewable_request = None
        self.session_id: Optional[int] = None
        self.auth_token = None
        self.repo_path = None

    async def pre_process_pr(self) -> (str, PullRequestDTO):
        repo_dto = await self.fetch_repo()
        setting = await self.fetch_setting()
        set_context_values(
            is_corrective_code_enabled=setting["code_review_agent"].get("is_corrective_code_enabled", False)
        )
        ContextValue.set(ContextValueKeys.PR_REVIEW_TOKEN.value, config.get("REVIEW_AUTH_TOKEN"))
        pr_state = self.pr_model.scm_state()
        # Declined and not raised by #review
        already_declined = pr_state == PRStatus.DECLINED.value and not get_context_value("manually_triggered_review")

        if already_declined or not self.is_reviewable_based_on_settings(setting):
            self.is_valid = False
            if already_declined:
                self.review_status = PrStatusTypes.REJECTED_ALREADY_DECLINED.value
            else:
                self.review_status = PrStatusTypes.FEATURES_DISABLED.value
            await self.run_validations()
            return False, self.pr_dto

        await self.insert_pr_record(repo_dto)
        await self.run_validations()

        experiment_set = await self.get_experiment_set()
        self.is_reviewable_request = self.get_is_reviewable_request(experiment_set)

    @staticmethod
    def is_reviewable_based_on_settings(setting: dict) -> bool:
        """Check if the PR is reviewable based on settings."""
        return setting["code_review_agent"]["enable"] or setting["pr_summary"]["enable"]

    async def fetch_setting(self) -> Dict[str, Any]:
        workspace_dto = await self.fetch_workspace()
        setting = await SettingService(self.repo_service, workspace_dto.team_id).build()
        return setting

    async def fetch_workspace(self) -> WorkspaceDTO:
        workspace_dto = await WorkspaceService.find(
            scm_workspace_id=self.pr_model.scm_workspace_id(), scm=self.pr_model.scm_type()
        )
        set_context_values(workspace_id=workspace_dto.id, team_id=workspace_dto.team_id)
        return workspace_dto

    def get_is_reviewable_request(self, experiment_set: str) -> bool:
        # if PR is eligible of experiment
        if ExperimentService.is_eligible_for_experiment() and experiment_set == PRReviewExperimentSet.ReviewTest.value:
            return True

        # If PR is not eligible for experiment
        if not ExperimentService.is_eligible_for_experiment() and self.is_valid:
            return True
        return False

    async def insert_pr_record(self, repo_dto: RepoDTO) -> None:
        self.pr_dto = await self.process_pr_record(repo_dto)
        if self.pr_dto:
            set_context_values(team_id=self.pr_dto.team_id)

    async def fetch_repo(self) -> RepoDTO:
        repo_dto = await RepoRepository.find_or_create_with_workspace_id(
            self.pr_model.scm_workspace_id(), self.pr_model
        )
        return repo_dto

    async def process_pr_record(self, repo_dto: RepoDTO) -> Optional[PullRequestDTO]:
        """Process PR record creation/update logic"""
        if not repo_dto:
            return None

        user_team_dto: UserTeamDTO = await UserTeamRepository.db_get(
            {"team_id": repo_dto.team_id, "is_owner": True}, fetch_one=True
        )
        if not user_team_dto or not user_team_dto.id:
            raise Exception("Owner not found for the team")

        # Check for existing reviewed PR
        reviewed_pr_dto = await self._get_reviewed_pr(repo_dto.id)

        if reviewed_pr_dto and reviewed_pr_dto.session_id:
            self.session_id = reviewed_pr_dto.session_id

        # Handle already reviewed PRs
        if reviewed_pr_dto and reviewed_pr_dto.commit_id == self.pr_model.commit_id():
            # Will be used to post affirmation message
            self.is_valid = False
            self.review_status = PrStatusTypes.ALREADY_REVIEWED.value
            return None

        # Set commit review context
        pr_reviewable_on_commit = False
        last_reviewed_commit = None
        feature_flow = FeatureFlows.INITIAL_CODE_REVIEW.value

        if reviewed_pr_dto:  # Got an entry with same destination branch
            review_full_pr = await self.should_do_full_review(reviewed_pr_dto.commit_id, self.pr_model.commit_id())
            # Signifies if it's initial code review or incremental code review for the PR
            feature_flow = FeatureFlows.INCREMENTAL_CODE_REVIEW.value
            if not review_full_pr:
                pr_reviewable_on_commit = True
                last_reviewed_commit = reviewed_pr_dto.commit_id

        set_context_values(
            pr_reviewable_on_commit=pr_reviewable_on_commit,
            last_reviewed_commit=last_reviewed_commit,
            feature_flow=feature_flow,
        )
        self.pr_diff_token_count = await self.pr_diff_handler.get_pr_diff_token_count()
        self.meta_info["tokens"] = self.pr_diff_token_count
        self.loc_changed = await self.pr_service.get_loc_changed_count()
        session = await MessageSessionsRepository.create_message_session(
            message_session_data=MessageSessionData(
                user_team_id=user_team_dto.id,
                client=Clients.BACKEND,
                client_version="1.0.0",
                session_type="PR_REVIEW",
            )
        )
        self.session_id = session.id

        # Check for failed PR
        failed_pr_filters = {
            "scm_pr_id": self.pr_model.scm_pr_id(),
            "repo_id": repo_dto.id,
            "review_status": PrStatusTypes.FAILED.value,
        }
        failed_pr_dto = await PRService.find(filters=failed_pr_filters)

        # Check for retries limit
        if failed_pr_dto and len(failed_pr_dto.session_ids) > config.get("ALLOWED_PR_REVIEW_RETRIES"):
            self.is_valid = False
            self.review_status = PrStatusTypes.EXHAUSTED_RETRIES_LIMIT.value
            return failed_pr_dto

        if failed_pr_dto:
            # Update failed PR
            update_data = {
                "commit_id": self.pr_model.commit_id(),
                "destination_commit_id": self.pr_model.destination_branch_commit(),
                "review_status": PrStatusTypes.IN_PROGRESS.value,
                "destination_branch": self.pr_model.destination_branch(),
                "loc_changed": self.loc_changed,
                "meta_info": self.meta_info,
                "session_id": self.session_id,
                "session_ids": failed_pr_dto.session_ids + [self.session_id],
            }
            return await PRService.db_update(filters={"id": failed_pr_dto.id}, payload=update_data)

        else:
            self.pr_model.meta_info = {
                "review_status": PrStatusTypes.IN_PROGRESS.value,
                "team_id": repo_dto.team_id,
                "workspace_id": repo_dto.workspace_id,
                "repo_id": repo_dto.id,
            }
            # Create new entry for PR
            pr_dto_data = {
                **self.pr_model.get_pr_info(),
                "pr_state": self.pr_model.scm_state(),
                "loc_changed": self.loc_changed,
                "session_id": self.session_id,
                "session_ids": [self.session_id],
            }
            pr_dto = await PRService.db_insert(PullRequestDTO(**pr_dto_data))
            if not pr_dto:  # Handle integrity error case
                self.is_valid = False
                self.review_status = PrStatusTypes.ALREADY_REVIEWED.value
                return None

            return pr_dto

    async def _get_reviewed_pr(self, repo_id: str) -> Optional[PullRequestDTO]:
        """Get previously reviewed PR if exists"""
        reviewed_pr_filters = {
            "scm_pr_id": self.pr_model.scm_pr_id(),
            "repo_id": repo_id,
            "destination_branch": self.pr_model.destination_branch(),
            "review_status__in": [
                PrStatusTypes.COMPLETED.value,
                PrStatusTypes.REJECTED_LARGE_SIZE.value,
                PrStatusTypes.REJECTED_NO_DIFF.value,
                PrStatusTypes.REJECTED_CLONING_FAILED_WITH_128.value,
                PrStatusTypes.REJECTED_INVALID_REQUEST.value,
                PrStatusTypes.EXHAUSTED_RETRIES_LIMIT.value,
            ],
        }
        return await PRService.find(filters=reviewed_pr_filters, order_by=["-iteration"])

    async def should_do_full_review(self, last_reviewed_commit: str, current_commit: str) -> bool:
        """
        Check if PR needs full review by detecting rebase or merge commits

        Args:
            last_reviewed_commit: Last reviewed commit hash
            current_commit: Current commit hash

        Returns:
            bool: True if PR should be fully reviewed (rebase detected or merge commits present)
        """
        commits = await self.pr_service.get_pr_commits()
        if not commits:
            return True

        current_commit_index = None
        last_review_commit_index = None

        # Find current commit and last commit index in PR commits
        for i, commit in enumerate(commits):
            if commit["hash"].startswith(current_commit):
                current_commit_index = i
            if commit["hash"].startswith(last_reviewed_commit):
                last_review_commit_index = i

        if last_review_commit_index is None:  # Rebased case, last reviewed commit not found in current pr commits
            return True

        # Checks if any commit in range is a merge commit with two or more than two parents
        return any(
            len(commit.get("parents", [])) > 1 for commit in commits[current_commit_index:last_review_commit_index]
        )

    async def run_validations(self) -> None:
        self.validate_pr_state_for_review()

        if self.is_valid:
            await self.validate_repo_clone()
        if self.is_valid:
            await self.validate_pr_diff()

        if not self.is_valid:
            if self.pr_dto:
                await self.update_pr_status(self.pr_dto)
            await self.process_invalid_prs()

    async def process_invalid_prs(self) -> None:
        await self.affirmation_service.create_affirmation_reply(
            message_type=self.review_status, commit_id=self.pr_model.commit_id()
        )

    async def validate_pr_diff(self) -> None:
        pr_diff = await self.pr_diff_handler.get_effective_pr_diff()
        if pr_diff == PR_NOT_FOUND:
            self.is_valid = False
            self.review_status = PrStatusTypes.REJECTED_INVALID_REQUEST.value
        elif pr_diff == "":
            self.is_valid = False
            self.review_status = PrStatusTypes.REJECTED_NO_DIFF.value
        elif pr_diff == LARGE_PR_DIFF or get_token_count(pr_diff) > MAX_PR_DIFF_TOKEN_LIMIT:
            await self.comment_service.create_pr_comment(
                comment=PR_SIZE_TOO_BIG_MESSAGE, model=config.get("FEATURE_MODELS").get("PR_REVIEW")
            )
            self.is_valid = False
            self.review_status = PrStatusTypes.REJECTED_LARGE_SIZE.value

    def validate_pr_state_for_review(self) -> None:
        pr_state = self.pr_model.scm_state()
        if ExperimentService.is_eligible_for_experiment():
            if pr_state == PRStatus.MERGED.value:
                self.is_valid = False
                self.review_status = PrStatusTypes.REJECTED_ALREADY_MERGED.value
            elif pr_state == PRStatus.DECLINED.value:
                self.is_valid = False
                self.review_status = PrStatusTypes.REJECTED_ALREADY_DECLINED.value

    async def get_experiment_set(self) -> str:
        if not ExperimentService.is_eligible_for_experiment() or not self.is_valid:
            return
        experiment_info = await ExperimentService.db_get({"repo_id": self.pr_dto.repo_id, "pr_id": self.pr_dto.id})
        experiment_set = (
            experiment_info.cohort if experiment_info else await ExperimentService.initiate_experiment(self.pr_dto)
        )
        if experiment_set != PRReviewExperimentSet.ReviewTest.value:
            self.review_status = PrStatusTypes.REJECTED_EXPERIMENT.value
            await self.update_pr_status(self.pr_dto)
            await self.update_pr_experiment_status(self.pr_dto.id, ExperimentStatusTypes.COMPLETED.value)
        return experiment_set

    async def update_pr_status(self, pr_dto: PullRequestDTO) -> None:
        self.completed_pr_count = await PRService.get_completed_pr_count(pr_dto)

        await PRService.db_update(
            payload={
                "review_status": self.review_status,
                "meta_info": self.meta_info if self.meta_info else None,
                "iteration": self.completed_pr_count + 1,
                "loc_changed": self.loc_changed,
            },
            filters={"id": pr_dto.id},
        )

    async def update_pr_experiment_status(self, pr_id: int, status: str) -> None:
        await ExperimentService.db_update(
            payload={"review_status": status},
            filters={"pr_id": pr_id},
        )

    async def validate_repo_clone(self) -> None:
        _, is_repo_cloned, self.repo_path = await self.repo_service.clone_branch(
            self.pr_service.branch_name, "code_review"
        )  # return code 128 signifies bad request to github
        set_context_values(repo_path=self.repo_path)
        if not is_repo_cloned:
            self.is_valid = False
            self.review_status = PrStatusTypes.REJECTED_CLONING_FAILED_WITH_128.value

    async def handle_non_reviewable_request(self, data: Dict[str, Any]) -> None:
        """Handle non-reviewable requests by creating appropriate notifications and DB entries.

        Args:
            data (Dict[str, Any]): Dictionary containing necessary data for processing the request.
        """
        try:
            await self.create_non_reviewable_pr_entry(data)
        except Exception as ex:
            AppLogger.log_error(f"Error while processing non-reviewable request: {ex}")
            raise ex

    async def create_non_reviewable_pr_entry(self, data: Dict[str, Any]) -> Optional[PullRequestDTO]:
        """Create DB entry for non-reviewable PR similar to pre_processor logic."""
        try:
            pr_model = self.pr_service.pr_model()
            repo_dto = await RepoRepository.find_or_create_with_workspace_id(pr_model.scm_workspace_id(), pr_model)
            if not repo_dto:
                return

            user_team_dto: UserTeamDTO = await UserTeamRepository.db_get(
                {"team_id": repo_dto.team_id, "is_owner": True}, fetch_one=True
            )
            if not user_team_dto or not user_team_dto.id:
                raise Exception("Owner not found for the team")
            loc_changed = await self.pr_service.get_loc_changed_count()

            pr_model.meta_info = {
                "review_status": PrStatusTypes.SKIPPED_AUTO_REVIEW.value,
                "team_id": repo_dto.team_id,
                "workspace_id": repo_dto.workspace_id,
                "repo_id": repo_dto.id,
            }

            pr_dto_data = {
                **pr_model.get_pr_info(),
                "pr_state": pr_model.scm_state(),
                "loc_changed": loc_changed,
            }
            pr_dto = await PRService.db_insert(PullRequestDTO(**pr_dto_data))
            return pr_dto

        except Exception as ex:
            AppLogger.log_error(f"Error creating non-reviewable PR entry: {ex}")
            raise ex
