import json
from datetime import datetime
from typing import Dict, List, Optional

from sanic.log import logger

from app.backend_common.constants.past_workflows import SessionStatus
from app.backend_common.models.dao.postgres.extension_sessions import ExtensionSession
from app.backend_common.models.dto.extension_sessions_dto import (
    ExtensionSessionData,
    ExtensionSessionDTO,
)
from app.backend_common.repository.db import DB
from deputydev_core.llm_handler.models.dto.message_thread_dto import LLModels


class ExtensionSessionsRepository:
    @classmethod
    async def get_by_id(
        cls,
        session_id: int,
    ) -> Optional[ExtensionSessionDTO]:
        try:
            extension_session = await DB.by_filters(
                model_name=ExtensionSession,
                where_clause={"session_id": session_id},
                fetch_one=True,
            )
            if not extension_session:
                return None
            return ExtensionSessionDTO(**extension_session)

        except Exception as ex:
            logger.error(
                f"error occurred while fetching extension_session from db for session_id filters : {session_id}, ex: {ex}"
            )
            raise ex

    @classmethod
    async def create_extension_session(cls, extension_session_data: ExtensionSessionData) -> ExtensionSessionDTO:
        try:
            extension_session = await DB.create(ExtensionSession, extension_session_data.model_dump(mode="json"))
            return ExtensionSessionDTO.model_validate_json(
                json_data=json.dumps(
                    dict(
                        id=extension_session.id,
                        session_id=extension_session.session_id,
                        user_team_id=extension_session.user_team_id,
                        summary=extension_session.summary,
                        pinned_rank=extension_session.pinned_rank,
                        status=extension_session.status,
                        session_type=extension_session.session_type,
                        created_at=extension_session.created_at.isoformat(),
                        updated_at=extension_session.updated_at.isoformat(),
                        current_model=extension_session.current_model,
                    )
                )
            )

        except Exception as ex:
            logger.error(
                f"error occurred while creating extension_session in db for extension_session_data : {extension_session_data}, ex: {ex}"
            )
            raise ex

    @classmethod
    async def find_or_create(cls, session_id: int, user_team_id: int, session_type: str) -> ExtensionSessionDTO:
        extension_session = await cls.get_by_id(session_id)
        if not extension_session:
            extension_session_data = ExtensionSessionData(
                session_id=session_id,
                user_team_id=user_team_id,
                session_type=session_type,
            )
            extension_session = await cls.create_extension_session(extension_session_data)
        return extension_session

    @classmethod
    async def update_session_summary(cls, session_id: int, summary: str) -> None:
        try:
            await DB.update_by_filters(None, ExtensionSession, {"summary": summary}, {"session_id": session_id})
        except Exception as ex:
            logger.error(f"error occurred while updating extension_session in DB, ex: {ex}")
            raise ex

    @classmethod
    async def get_extension_sessions_ids(
        cls,
        user_team_id: int,
        session_type: Optional[str] = None,
    ) -> List[int]:
        try:
            filters = {"user_team_id": user_team_id, "session_type": session_type}
            extension_sessions = await DB.by_filters(
                model_name=ExtensionSession,
                where_clause=filters,
                fetch_one=False,
            )
            if not extension_sessions:
                return []

            # Return only the IDs of the extension sessions
            return [extension_session["session_id"] for extension_session in extension_sessions]

        except Exception as ex:  # noqa: BLE001
            logger.error(
                f"error occurred while fetching extension_sessions from db for user_team_id filters : {user_team_id}, ex: {ex}"
            )
            return []

    @classmethod
    async def get_extension_sessions_by_user_team_id(
        cls,
        user_team_id: int,
        session_type: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        pinned_rank_is_null: bool = False,
    ) -> List[ExtensionSessionDTO]:
        if not limit:
            limit = 5
        if not offset:
            offset = 0
        try:
            filters = {
                "user_team_id": user_team_id,
                "status": SessionStatus.ACTIVE.value,
                "pinned_rank__isnull": pinned_rank_is_null,
            }
            if session_type:
                filters["session_type"] = session_type

            extension_sessions = await DB.by_filters(
                model_name=ExtensionSession,
                where_clause=filters,
                fetch_one=False,
                limit=limit,
                offset=offset,
                order_by=["-updated_at"] if pinned_rank_is_null else ["pinned_rank"],
            )
            if not extension_sessions:
                return []
            return [ExtensionSessionDTO(**extension_session) for extension_session in extension_sessions]

        except Exception as ex:  # noqa: BLE001
            logger.error(
                f"error occurred while fetching extension_sessions from db for user_team_id filters : {user_team_id}, ex: {ex}"
            )
            return []

    @classmethod
    async def soft_delete_extension_session_by_id(cls, session_id: int, user_team_id: int) -> None:
        try:
            # First check if the session belongs to the user
            extension_session = await DB.by_filters(
                model_name=ExtensionSession,
                where_clause={"session_id": session_id, "user_team_id": user_team_id},
                fetch_one=True,
            )
            if not extension_session:
                raise ValueError("Session not found or you don't have permission to delete it")

            # Soft delete the session
            await DB.update_by_filters(
                None,
                ExtensionSession,
                {"status": SessionStatus.DELETED.value, "deleted_at": datetime.now()},
                {"session_id": session_id},
            )
        except (ValueError, Exception) as ex:
            logger.error(f"error occurred while soft deleting extension_session in DB, ex: {ex}")
            raise ex

    @classmethod
    async def update_pinned_rank_by_session_ids(cls, user_team_id: int, sessions_data: Dict[int, int]) -> None:
        try:
            if not sessions_data:
                raise ValueError("No sessions data provided")

            case_statements = " ".join(
                f"WHEN {session_id} THEN {pinned_rank}" for session_id, pinned_rank in sessions_data.items()
            )

            session_ids = ", ".join(str(session_id) for session_id in sessions_data.keys())

            query = f"""
                UPDATE extension_sessions
                SET pinned_rank = CASE session_id
                    {case_statements}
                END
                WHERE session_id IN ({session_ids})
                AND user_team_id = {user_team_id};
            """

            await DB.execute_raw_sql(query)
        except Exception as ex:
            logger.error(f"Error occurred while updating extension_session on drag in DB: {ex}")
            raise ex

    @classmethod
    async def update_session_pinned_rank(
        cls, session_id: int, user_team_id: int, pinned_rank: Optional[int] = None
    ) -> None:
        try:
            # First check if the session belongs to the user
            extension_session = await DB.by_filters(
                model_name=ExtensionSession,
                where_clause={"session_id": session_id, "user_team_id": user_team_id},
                fetch_one=True,
            )
            if not extension_session:
                raise ValueError("Session not found or you don't have permission to delete it")

            # Update the pinned rank
            await DB.update_by_filters(
                None,
                ExtensionSession,
                {"pinned_rank": pinned_rank},
                {"session_id": session_id},
            )
        except (ValueError, Exception) as ex:
            logger.error(f"error occurred while updating extension_session in DB, ex: {ex}")
            raise ex

    @classmethod
    async def get_unmigrated_sessions(cls, limit: int) -> List[ExtensionSessionDTO]:
        try:
            extension_sessions = await DB.by_filters(
                model_name=ExtensionSession,
                # get where current model is null and summary is not null
                where_clause={"current_model__isnull": True, "summary__isnull": False},
                fetch_one=False,
                limit=limit,
            )
            if not extension_sessions:
                return []
            return [ExtensionSessionDTO(**extension_session) for extension_session in extension_sessions]

        except Exception as ex:  # noqa: BLE001
            logger.error(f"error occurred while fetching unmigrated extension_sessions from db, ex: {ex}")
            return []

    @classmethod
    async def update_session_llm_model(cls, session_id: int, llm_model: LLModels) -> None:
        try:
            await DB.update_by_filters(
                None,
                ExtensionSession,
                {"current_model": llm_model.value},
                {"session_id": session_id},
            )
        except Exception as ex:
            logger.error(f"error occurred while updating extension_session in DB, ex: {ex}")
            raise ex
