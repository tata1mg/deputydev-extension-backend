from datetime import datetime
from typing import List, Optional, Tuple

from app.backend_common.models.dto.extension_sessions_dto import ExtensionSessionDTO
from app.backend_common.repository.extension_sessions.repository import (
    ExtensionSessionsRepository,
)
from app.main.blueprints.one_dev.services.history.sessions.dataclasses.sessions import (
    FormattedSession,
    PastSessionsInput,
    PinnedRankUpdateInput,
    SessionsListTypes,
)


class PastSessionsManager:
    """
    A class to handle operations related to past workflows, including fetching past sessions and chats.
    """

    @classmethod
    def _get_formatted_age(cls, current_time: datetime, updated_at: datetime) -> str:
        """
        Calculates the age of a message session based on the current time and its creation time.

        Args:
            current_time (datetime): The current time.
            updated_at (datetime): The creation time of the message session.

        Returns:
            str: A string representing the age in minutes, hours, or days.
        """
        age_in_seconds = (current_time - updated_at).total_seconds()
        if age_in_seconds < 60:
            return f"{int(age_in_seconds)}s"
        elif age_in_seconds < 3600:
            age_in_minutes = age_in_seconds / 60
            return f"{int(age_in_minutes)}m"
        elif age_in_seconds < 86400:
            age_in_hours = age_in_seconds / 3600
            return f"{int(age_in_hours)}h"
        else:
            age_in_days = age_in_seconds / 86400
            return f"{int(age_in_days)}d"

    @classmethod
    def _get_formatted_past_sessions(
        cls,
        raw_data: List[ExtensionSessionDTO],
    ) -> List[FormattedSession]:
        """
        Processes raw message session data and formats it for output.

        Args:
            raw_data (List[ExtensionSessionDTO]): The raw message session data to be processed.
            type (SerializerTypes): The type of data being serialized.

        Returns:
            List[Dict[str, Any]]: A list of formatted message session data.
        """
        formatted_data: List[FormattedSession] = []
        current_time = datetime.now()
        for item in raw_data:
            if item.summary:
                formatted_data.append(
                    FormattedSession(
                        id=item.session_id,
                        summary=item.summary,
                        age=cls._get_formatted_age(current_time, item.updated_at),
                        pinned_rank=item.pinned_rank,
                        created_at=item.created_at.isoformat(),
                        updated_at=item.updated_at.isoformat(),
                    )
                )
        return formatted_data

    @classmethod
    async def get_past_sessions(cls, payload: PastSessionsInput) -> Tuple[List[FormattedSession], bool]:
        """
        Fetch past sessions for a given user team ID.

        Args:
            user_team_id (int): The ID of the user team.
            session_type (str): The type of session to fetch.
            sessions_list_type (str): The type of sessions list to fetch (PINNED or UNPINNED).
            limit (Optional[int]): Maximum number of sessions to return. Defaults to None.
                If sessions_list_type is UNPINNED, one extra item is fetched to determine if there are more items.
            offset (Optional[int]): Offset for pagination. Defaults to None.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - "sessions": List of processed session data (List[Dict[str, Any]])
                - "has_more": Boolean indicating if there are more sessions available
                    This is only applicable when sessions_list_type is UNPINNED.

        Raises:
            ValueError: If sessions_list_type is not PINNED or UNPINNED.
            NotImplementedError: If the serializer method is not implemented.
            Exception: For any other errors encountered during the process.
        """
        has_more: bool = False
        if payload.sessions_list_type == SessionsListTypes.PINNED:
            pinned_rank_is_null = False
        elif payload.sessions_list_type == SessionsListTypes.UNPINNED:
            pinned_rank_is_null = True
        else:
            raise ValueError("Invalid sessions list type")

        limit_to_use: Optional[int] = None
        if payload.sessions_list_type == SessionsListTypes.UNPINNED:
            if not payload.limit:
                raise ValueError("Limit must be provided for UNPINNED sessions")
            limit_to_use = payload.limit + 1  # Fetch one extra item to check for more items

        else:
            limit_to_use = payload.limit

        raw_data = await ExtensionSessionsRepository.get_extension_sessions_by_user_team_id(
            user_team_id=payload.user_team_id,
            limit=limit_to_use,
            offset=payload.offset,
            session_type=payload.session_type,
            pinned_rank_is_null=pinned_rank_is_null,
        )
        if limit_to_use and len(raw_data) > limit_to_use - 1:
            has_more = True
            raw_data = raw_data[: limit_to_use - 1]
        processed_data = cls._get_formatted_past_sessions(raw_data=raw_data)
        return processed_data, has_more

    @classmethod
    async def update_pinned_rank(cls, payload: PinnedRankUpdateInput) -> None:
        """
        Updates the pinned rank of a session based on the specified sessions list type.

        This method checks if the sessions list type is either 'PINNED' or 'UNPINNED'.
        If 'PINNED', it retains the provided pinned rank; if 'UNPINNED', it sets the pinned rank to None.

        Args:
            session_id (int): The ID of the session to update.
            user_team_id (int): The ID of the user's team.
            sessions_list_type (str): The type of sessions list ('PINNED' or 'UNPINNED').
            pinned_rank (int): The new pinned rank to set for the session.

        Raises:
            ValueError: If the sessions list type is invalid.
        """
        pinned_rank_to_use: Optional[int] = None
        if payload.sessions_list_type == SessionsListTypes.PINNED:
            pinned_rank_to_use = payload.pinned_rank
        elif payload.sessions_list_type == SessionsListTypes.UNPINNED:
            pinned_rank_to_use = None
        else:
            raise ValueError("Invalid sessions list type")

        await ExtensionSessionsRepository.update_session_pinned_rank(
            session_id=payload.session_id, user_team_id=payload.user_team_id, pinned_rank=pinned_rank_to_use
        )
