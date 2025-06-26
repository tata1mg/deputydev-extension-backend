from typing import List, Union
from sanic.log import logger
from app.backend_common.models.dao.postgres.user_extension_repos import UserExtensionRepos
from app.backend_common.models.dto.user_extension_repo_dto import UserExtensionRepoDTO
from app.backend_common.repository.db import DB
from app.backend_common.services.encryption.user_extension_repo_encryption_service import UserExtensionRepoEncryptionService

class UserExtensionReposRepository:
    @classmethod
    async def db_get(cls, filters, fetch_one=False) -> Union[UserExtensionRepoDTO, List[UserExtensionRepoDTO]]:
        try:
            repo_data = await DB.by_filters(model_name=UserExtensionRepos, where_clause=filters, fetch_one=fetch_one)
            if repo_data and fetch_one:
                return UserExtensionRepoDTO(**repo_data)
            elif repo_data:
                return [UserExtensionRepoDTO(**repo) for repo in repo_data]
        except Exception as ex:
            logger.error(f"Error fetching user extension repo: {filters}, ex: {ex}")
            raise ex

    @classmethod
    async def db_insert(cls, repo_dto: UserExtensionRepoDTO):
        try:
            payload = repo_dto.dict()
            del payload["id"]
            row = await DB.insert_row(UserExtensionRepos, payload)
            return row
        except Exception as ex:
            logger.error(f"Error inserting user extension repo: {repo_dto.dict()}, ex: {ex}")
            raise ex

    @classmethod
    async def find_or_create(cls, user_team_id: int, repo_name: str, repo_path: str):
        repo_hash = UserExtensionRepoEncryptionService.generate_repo_hash(repo_name, repo_path)
        repo_dto = await cls.db_get(
            filters={"user_team_id": user_team_id, "repo_id": repo_hash}, fetch_one=True
        )
        if not repo_dto:
            repo_data = {
                "user_team_id": user_team_id,
                "repo_name": repo_name,
                "repo_id": repo_hash,
            }
            repo_dto = await cls.db_insert(UserExtensionRepoDTO(**repo_data))
        return repo_dto