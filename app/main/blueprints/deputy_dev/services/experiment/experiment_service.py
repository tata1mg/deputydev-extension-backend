from sanic.log import logger
from torpedo import CONFIG
from tortoise.expressions import F

from app.main.blueprints.deputy_dev.caches.ab_experiment import ABExperimentCache
from app.main.blueprints.deputy_dev.constants.constants import ExperimentStatusTypes
from app.main.blueprints.deputy_dev.models.dao import Experiments
from app.main.blueprints.deputy_dev.models.dto.experiments_dto import ExperimentsDTO
from app.main.blueprints.deputy_dev.models.dto.pr_dto import PullRequestDTO
from app.main.blueprints.deputy_dev.services.db.db import DB


class ExperimentService:
    """Service class to handle operations related to Experiments."""

    REVIEW_EXPERIMENT_CACHE_KEY = "{organisation_id}_{workspace_id}_{repo_id}"

    @classmethod
    async def db_insert(cls, experiment_dto: ExperimentsDTO) -> ExperimentsDTO:
        try:
            payload = experiment_dto.dict()
            del payload["id"]
            row = await DB.insert_row(Experiments, payload)
            if row:
                experiment_dto = ExperimentsDTO(**await row.to_dict())
                return experiment_dto
        except Exception as ex:
            logger.error("not able to insert Experiments data {} exception {}".format(experiment_dto.dict(), ex))
            raise ex

    @classmethod
    async def db_get(cls, filters: dict) -> ExperimentsDTO:
        try:
            experiments = await DB.by_filters(model_name=Experiments, where_clause=filters, limit=1, fetch_one=True)
            if experiments:
                return ExperimentsDTO(**experiments)
        except Exception as ex:
            logger.error(
                "error occurred while fetching Experiments details from db for "
                "experiment filters : {}, ex: {}".format(filters, ex)
            )
            raise ex

    @classmethod
    async def initiate_experiment(cls, pr_dto: PullRequestDTO):
        """
        Retrieve the experiment set for a given review cache key.

        Args:
            pr_dto (PullRequestDTO): The pull request data transfer object.

        Returns:
            dict: The configuration of the current experiment set.

        Raises:
            Exception: If fetching or setting cache fails.
        """
        review_cache_key = cls.REVIEW_EXPERIMENT_CACHE_KEY.format(
            organisation_id=pr_dto.organisation_id, workspace_id=pr_dto.workspace_id, repo_id=pr_dto.repo_id
        )
        experiment_config = CONFIG.config["REVIEW_PR_EXPERIMENT"]

        # Retrieve the cohort set index from the cache
        count = await ABExperimentCache.get(review_cache_key)

        # For first time or when redis is down
        if count is None:
            cohort_set_db_count = await cls.db_count(
                {"repo_id": pr_dto.repo_id, "organisation_id": pr_dto.organisation_id}
            )
            await ABExperimentCache.set(review_cache_key, cohort_set_db_count)

        count = await ABExperimentCache.incr(review_cache_key)
        experiment_set = experiment_config[(count - 1) % len(CONFIG.config["REVIEW_PR_EXPERIMENT"])]

        experiment_info = {
            "organisation_id": pr_dto.organisation_id,
            "workspace_id": pr_dto.workspace_id,
            "repo_id": pr_dto.repo_id,
            "scm_pr_id": pr_dto.scm_pr_id,
            "scm": pr_dto.scm,
            "cohort": experiment_set,
            "review_status": ExperimentStatusTypes.IN_PROGRESS.value,
            "pr_id": pr_dto.id,
            "scm_creation_time": pr_dto.scm_creation_time,
            "pr_state": pr_dto.pr_state,
        }
        await ExperimentService.db_insert(ExperimentsDTO(**experiment_info))

        return experiment_set

    @classmethod
    async def db_count(cls, filters) -> int:
        """
        Get the count of pull requests for a given workspace and organization.

        Args:
            pr_dto (PullRequestDTO): The pull request data transfer object.

        Returns:
            int: The count of pull requests.
        """
        try:
            experiments_count = await DB.get_by_filters_count(model=Experiments, filters=filters)
            return experiments_count
        except Exception as ex:
            logger.error(
                "error occurred while fetching Experiments counts from db for "
                "experiment filters : {}, ex: {}".format(filters, ex)
            )
            raise ex

    @classmethod
    async def db_update(cls, payload, filters):
        try:
            row = await DB.update_by_filters(None, Experiments, payload, where_clause=filters)
            return row
        except Exception as ex:
            logger.error("not able to update pr details {}  exception {}".format(payload, ex))
            raise ex

    @classmethod
    async def get_data_in_range(cls, start, end):
        try:
            row = await DB.get_by_filters(model=Experiments, filters={"id__gte": start, "id__lte": end})
            return row
        except Exception as ex:
            logger.error("Not able to fetch experiment data range - {}".format(ex))
            raise ex

    @classmethod
    async def increment_human_comment_count(cls, scm_pr_id, repo_id):
        query = (
            f"UPDATE experiments SET human_comment_count = COALESCE(human_comment_count, 0) + 1 "
            f"WHERE scm_pr_id = '{scm_pr_id}' AND repo_id = {repo_id} RETURNING human_comment_count;"
        )
        update_count = await DB.raw_sql(query)
        if update_count:
            return True
        return False

    @classmethod
    async def decrement_human_comment_count(cls, scm_pr_id, repo_id):
        update_count = await Experiments.filter(scm_pr_id=scm_pr_id, repo_id=repo_id).update(
            human_comment_count=F("human_comment_count") - 1
        )
        return update_count
