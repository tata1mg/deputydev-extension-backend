from typing import Any, Dict, List, Optional

from app.backend_common.models.dto.message_thread_dto import MessageCallChainCategory
from app.backend_common.repository.message_sessions.repository import (
    MessageSessionsRepository,
)
from app.backend_common.repository.message_threads.repository import (
    MessageThreadsRepository,
)
from app.main.blueprints.one_dev.services.past_workflows.constants.serializer_constants import (
    SerializerTypes,
)
from app.main.blueprints.one_dev.services.past_workflows.serializer.serializers_factory import (
    SerializersFactory,
)


class PastWorkflows:
    """
    A class to handle operations related to past workflows, including fetching past sessions and chats.
    """

    @classmethod
    async def get_past_sessions(
        cls, user_team_id: int, session_type: str, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch past sessions for a given user team ID.

        Args:
            headers (Dict[str, Any]): The headers containing the user team ID.

        Returns:
            List[Dict[str, Any]]: A list of processed past session data.

        Raises:
            ValueError: If there is an issue with the input or data retrieval.
            NotImplementedError: If the serializer method is not implemented.
            Exception: For any other errors encountered during the process.
        """
        print(session_type)
        print(user_team_id)
        print(limit)
        print(offset)
        raw_data = await MessageSessionsRepository.get_message_sessions_by_user_team_id(
            user_team_id=user_team_id, limit=limit, offset=offset, session_type=session_type
        )
        serializer_service = SerializersFactory.get_serializer_service(raw_data, SerializerTypes.PAST_SESSIONS)
        processed_data = serializer_service.get_processed_data()
        print(processed_data)
        return processed_data

    @classmethod
    async def get_past_chats(cls, session_id: int) -> List[Dict[str, Any]]:
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
        processed_data = serializer_service.get_processed_data()
        return processed_data
