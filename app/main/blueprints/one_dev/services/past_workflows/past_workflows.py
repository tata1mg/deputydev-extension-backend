
from app.backend_common.models.dto.message_thread_dto import MessageCallChainCategory
from app.backend_common.repository.message_sessions.repository import MessageSessionsRepository
from app.backend_common.repository.message_threads.repository import MessageThreadsRepository
from app.main.blueprints.one_dev.constants.serializers_constants import SerializerTypes
from app.main.blueprints.one_dev.services.past_workflows.serializer.serializers_factory import SerializersFactory
from typing import List, Dict, Any

class PastWorkflows():
    """
    A class to handle operations related to past workflows, including fetching past sessions and chats.
    """

    @classmethod
    async def get_past_sessions(cls, user_team_id: int) -> List[Dict[str, Any]]:
        """
        Fetch past sessions for a given user team ID.

        Args:
            user_team_id (int): The ID of the user team for which to fetch past sessions.

        Returns:
            List[Dict[str, Any]]: A list of processed past session data.

        Raises:
            ValueError: If there is an issue with the input or data retrieval.
            NotImplementedError: If the serializer method is not implemented.
            Exception: For any other errors encountered during the process.
        """
        try:
            raw_data = await MessageSessionsRepository.get_message_sessions_by_user_team_id(user_team_id)
            serializer_service = SerializersFactory.get_serializer_service(raw_data, SerializerTypes("past_sessions"))
            processed_data = serializer_service.get_processed_data()
            return processed_data
        except ValueError as ve:
            raise ValueError(f"Failed to fetch past sessions: {str(ve)}")
        except NotImplementedError as nie:
            raise NotImplementedError(f"Failed to fetch past sessions: {str(nie)}")
        except Exception as e:
            raise Exception(f"Failed to fetch past sessions: {str(e)}")

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
        try:
            raw_data = await MessageThreadsRepository.get_message_threads_for_session(session_id, call_chain_category=MessageCallChainCategory("CLIENT_CHAIN"))
            serializer_service = SerializersFactory.get_serializer_service(raw_data, SerializerTypes("past_chats"))
            processed_data = serializer_service.get_processed_data()
            return processed_data
        except ValueError as ve:
            raise ValueError(f"Failed to fetch past chats: {str(ve)}")
        except NotImplementedError as nie:
            raise NotImplementedError(f"Failed to fetch past chats: {str(nie)}")
        except Exception as e:
            raise Exception(f"Failed to fetch past chats: {str(e)}")
