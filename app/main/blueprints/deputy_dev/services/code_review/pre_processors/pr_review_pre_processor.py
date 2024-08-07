from app.main.blueprints.deputy_dev.constants.constants import (
    MAX_PR_DIFF_TOKEN_LIMIT,
    PR_SIZE_TOO_BIG_MESSAGE,
    ExperimentStatusTypes,
    LLMModels,
    PRReviewExperimentSet,
    PRStatus,
    PrStatusTypes,
    TokenTypes,
)
from app.main.blueprints.deputy_dev.constants.repo import PR_NOT_FOUND
from app.main.blueprints.deputy_dev.models.dto.pr_dto import PullRequestDTO
from app.main.blueprints.deputy_dev.services.comment.base_comment import BaseComment
from app.main.blueprints.deputy_dev.services.experiment.experiment_service import (
    ExperimentService,
)
from app.main.blueprints.deputy_dev.services.pr.pr_service import PRService
from app.main.blueprints.deputy_dev.services.repo.base_repo import BaseRepo


class PRReviewPreProcessor:
    def __init__(self, repo_service: BaseRepo, comment_service: BaseComment):
        self.repo_service = repo_service
        self.comment_service = comment_service
        self.pr_model = repo_service.pr_model()
        self.experiment_set = None
        self.is_valid = True
        self.review_status = PrStatusTypes.IN_PROGRESS.value
        self.tokens_info = {}
        self.meta_info = {}
        self.pr_dto = None
        self.pr_diff_token_count = None

    async def pre_process_pr(self) -> (str, PullRequestDTO):
        await self.insert_pr_record()
        await self.run_validations()
        experiment_set = await self.get_experiment_set()
        return experiment_set, self.pr_dto

    async def insert_pr_record(self):
        self.pr_diff_token_count = await self.repo_service.get_pr_diff_token_count()
        self.meta_info["tokens"] = {TokenTypes.PR_DIFF_TOKENS.value: self.pr_diff_token_count}
        loc_changed = await self.repo_service.get_loc_changed_count()
        self.pr_dto = await PRService.find_or_create(
            self.pr_model, PrStatusTypes.IN_PROGRESS.value, loc_changed, self.meta_info
        )

    async def run_validations(self):
        self.validate_pr_state_for_review()
        if self.is_valid:
            await self.validate_pr_diff()
            if self.is_valid:
                await self.validate_repo_clone()
        if not self.is_valid:
            await self.update_pr_status(self.pr_dto.id)

    async def validate_pr_diff(self):
        pr_diff = await self.repo_service.get_pr_diff()
        if pr_diff == PR_NOT_FOUND:
            self.is_valid = False
            self.review_status = PrStatusTypes.REJECTED_INVALID_REQUEST.value
        elif pr_diff == "":
            self.is_valid = False
            self.review_status = PrStatusTypes.REJECTED_NO_DIFF.value
        else:
            if self.pr_diff_token_count > MAX_PR_DIFF_TOKEN_LIMIT:
                comment = PR_SIZE_TOO_BIG_MESSAGE.format(
                    pr_diff_token_count=self.pr_diff_token_count, max_token_limit=MAX_PR_DIFF_TOKEN_LIMIT
                )
                await self.comment_service.create_pr_comment(comment=comment, model=LLMModels.FoundationModel.value)
                self.is_valid = False
                self.review_status = PrStatusTypes.REJECTED_LARGE_SIZE.value

    def validate_pr_state_for_review(self):
        pr_state = self.pr_model.scm_state()

        if pr_state == PRStatus.MERGED.value:
            self.is_valid = False
            self.review_status = PrStatusTypes.REJECTED_ALREADY_MERGED.value
        elif pr_state == PRStatus.DECLINED.value:
            self.is_valid = False
            self.review_status = PrStatusTypes.REJECTED_ALREADY_DECLINED.value

    async def get_experiment_set(self):
        if not self.is_valid:
            return
        experiment_info = await ExperimentService.db_get({"repo_id": self.pr_dto.repo_id, "pr_id": self.pr_dto.id})
        experiment_set = (
            experiment_info.cohort if experiment_info else await ExperimentService.initiate_experiment(self.pr_dto)
        )
        if experiment_set != PRReviewExperimentSet.ReviewTest.value:
            self.review_status = PrStatusTypes.REJECTED_EXPERIMENT.value
            await self.update_pr_status(self.pr_dto.id)
            await self.update_pr_experiment_status(self.pr_dto.id, ExperimentStatusTypes.COMPLETED.value)
        return experiment_set

    async def update_pr_status(self, pr_id):
        await PRService.db_update(
            payload={
                "review_status": self.review_status,
                "meta_info": self.meta_info if self.meta_info else None,
            },
            filters={"id": pr_id},
        )

    async def update_pr_experiment_status(self, pr_id, status):
        await ExperimentService.db_update(
            payload={"review_status": status},
            filters={"pr_id": pr_id},
        )

    async def validate_repo_clone(self):
        _, is_repo_cloned = await self.repo_service.clone_repo()  # return code 128 signifies bad request to github
        if not is_repo_cloned:
            self.is_valid = False
            self.review_status = PrStatusTypes.REJECTED_CLONING_FAILED_WITH_128.value
