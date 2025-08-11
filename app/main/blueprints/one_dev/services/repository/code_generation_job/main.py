from typing import Any, Dict, List, Union

from sanic.log import logger

from app.backend_common.repository.db import DB
from app.main.blueprints.one_dev.models.dao.postgres.job import Job
from app.main.blueprints.one_dev.models.dto.job import JobDTO


class JobService:
    @classmethod
    async def db_get(cls, filters: Dict[str, Any], fetch_one: bool = False) -> Union[List[JobDTO], JobDTO]:
        try:
            code_generation_jobs = await DB.by_filters(model_name=Job, where_clause=filters, fetch_one=False)
            if code_generation_jobs and fetch_one:
                return JobDTO(**code_generation_jobs[0])
            elif code_generation_jobs:
                return [JobDTO(**code_generation_job) for code_generation_job in code_generation_jobs]
            else:
                raise ValueError("No job found")
        except Exception as ex:  # noqa: BLE001
            logger.error(
                "error occurred while fetching sessionchat details from db for sessionchat filters : {}, ex: {}".format(
                    filters, ex
                )
            )

    @classmethod
    async def db_create(cls, code_generation_job: JobDTO) -> JobDTO:
        try:
            payload = code_generation_job.model_dump(mode="json")
            del payload["id"]
            del payload["created_at"]
            del payload["updated_at"]
            row = await DB.create(model=Job, payload=payload)
            return JobDTO(**(await row.to_dict()))
        except Exception as ex:
            logger.exception(
                "error occurred while creating job details in db for job : {}, ex: {}".format(code_generation_job, ex)
            )
            raise ex

    @classmethod
    async def db_update(cls, filters: Dict[str, Any], update_data: Dict[str, Any]) -> None:
        try:
            await DB.update_by_filters(row=None, model_name=Job, where_clause=filters, payload=update_data)
        except Exception as ex:
            logger.exception(
                "error occurred while updating job details in db for job : {}, ex: {}".format(update_data, ex)
            )
            raise ex
