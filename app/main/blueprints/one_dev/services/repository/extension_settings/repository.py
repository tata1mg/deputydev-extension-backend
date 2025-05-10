import json
from typing import Optional

from sanic.log import logger

from app.backend_common.repository.db import DB
from app.main.blueprints.one_dev.models.dao.postgres.extension_settings import (
    ExtensionSetting,
)
from app.main.blueprints.one_dev.models.dto.extension_settings_dto import (
    ExtensionSettingsData,
    ExtensionSettingsDTO,
)


class ExtensionSettingsRepository:
    @classmethod
    async def get_extension_settings_by_user_team_id(cls, user_team_id: int) -> Optional[ExtensionSettingsDTO]:
        try:
            extension_settings = await DB.by_filters(
                model_name=ExtensionSetting,
                where_clause={"user_team_id": user_team_id},
                fetch_one=True,
            )
            if not extension_settings:
                return None
            return ExtensionSettingsDTO(**extension_settings)
        except Exception as ex:
            logger.error(
                f"error occurred while getting extension_settings in db for user_team_id : {user_team_id}, ex: {ex}"
            )
            raise ex

    @classmethod
    async def update_or_create_extension_settings(cls, extension_settings_data: ExtensionSettingsData) -> None:
        try:
            if await cls.get_extension_settings_by_user_team_id(extension_settings_data.user_team_id):
                await DB.update_with_filters(
                    None,
                    model=ExtensionSetting,
                    payload={"settings": extension_settings_data.settings.model_dump(mode="json")},
                    where_clause={"user_team_id": extension_settings_data.user_team_id},
                    update_fields=["settings", "updated_at"],
                )
            else:
                await DB.create(ExtensionSetting, extension_settings_data.model_dump(mode="json"))
        except Exception as ex:
            logger.error(
                f"error occurred while creating/updating extension_settings in db for user_team_id : {extension_settings_data.user_team_id}, ex: {ex}"
            )
            raise ex
