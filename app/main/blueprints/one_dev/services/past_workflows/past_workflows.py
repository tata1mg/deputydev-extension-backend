from typing import Any, Dict, List, Optional, Union

from app.backend_common.models.dto.message_thread_dto import MessageCallChainCategory
from app.backend_common.repository.extension_sessions.repository import (
    ExtensionSessionsRepository,
)
from app.backend_common.repository.message_threads.repository import (
    MessageThreadsRepository,
)
from app.main.blueprints.one_dev.services.past_workflows.constants.serializer_constants import (
    SerializerTypes,
    SessionsListTypes,
)
from app.main.blueprints.one_dev.services.past_workflows.serializer.serializers_factory import (
    SerializersFactory,
)
from app.main.blueprints.one_dev.utils.client.dataclasses.main import ClientData
from app.main.blueprints.one_dev.utils.version import compare_version


class PastWorkflows:
    """
    A class to handle operations related to past workflows, including fetching past sessions and chats.
    """

    @classmethod
    async def get_past_sessions(
        cls,
        user_team_id: int,
        client_data: ClientData,
        session_type: str,
        sessions_list_type: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
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
        if SessionsListTypes(sessions_list_type) == SessionsListTypes.PINNED:
            pinned_rank_is_null = False
        elif SessionsListTypes(sessions_list_type) == SessionsListTypes.UNPINNED:
            pinned_rank_is_null = True
        else:
            raise ValueError("Invalid sessions list type")

        raw_data = await ExtensionSessionsRepository.get_extension_sessions_by_user_team_id(
            user_team_id=user_team_id,
            limit=limit + 1 if SessionsListTypes(sessions_list_type) == SessionsListTypes.UNPINNED else limit,
            offset=offset,
            session_type=session_type,
            pinned_rank_is_null=pinned_rank_is_null,
        )
        if SessionsListTypes(sessions_list_type) == SessionsListTypes.UNPINNED:
            has_more = len(raw_data) > limit
            raw_data = raw_data[:limit]
        serializer_service = SerializersFactory.get_serializer_service(raw_data, SerializerTypes.PAST_SESSIONS)
        processed_data = await serializer_service.get_processed_data()
        if compare_version(client_data.client_version, "2.0.1", "<="):
            return processed_data
        return {
            "sessions": processed_data,
            "has_more": has_more,
        }

    @classmethod
    async def get_past_chats(cls, session_id: int, client_data: Optional[ClientData]= None) -> List[Dict[str, Any]]:
        """
        Fetch past chats.

        Returns:
            List[Dict[str, Any]]: A list of processed past chat data.

        Raises:
            ValueError: If there is an issue with the data retrieval.
            NotImplementedError: If the serializer method is not implemented.
            Exception: For any other errors encountered during the process.
        """
        raw_data = await MessageThreadsRepository.get_message_threads_for_session(
            session_id, call_chain_category=MessageCallChainCategory("CLIENT_CHAIN")
        )
        serializer_service = SerializersFactory.get_serializer_service(raw_data, SerializerTypes("PAST_CHATS"))
        processed_data = await serializer_service.get_processed_data(client_data=client_data)
        return processed_data

    @classmethod
    async def update_pinned_rank(
        cls, session_id: int, user_team_id: int, sessions_list_type: str, pinned_rank: int
    ) -> None:
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
        if SessionsListTypes(sessions_list_type) == SessionsListTypes.PINNED:
            pinned_rank = pinned_rank
        elif SessionsListTypes(sessions_list_type) == SessionsListTypes.UNPINNED:
            pinned_rank = None
        else:
            raise ValueError("Invalid sessions list type")

        await ExtensionSessionsRepository.update_session_pinned_rank(session_id, user_team_id, pinned_rank)
