

from app.dao.labsConn import LabsConn
from app.constants.constants import Augmentation
from app.models.chat import ChatModel, ChatTypeMsg
from app.routes.end_user.headers import Headers
from app.managers.serializer.initialize_jiva_serializer import InitializeJivaSerializer
from app.utils import get_ab_experiment_set
from torpedo import Task

from app.managers.bots.bot_response_factory import BotResponseFactory


class JivaManager:
    def __init__(self):
        self.store = LabsConn().get_store()
        self.query_context = ""

    @staticmethod
    async def show_boat_based_on_ab(headers: Headers):
        show_nudge = False
        experiment = get_ab_experiment_set(headers.visitor_id(), "JIVA_EXPERIMENT")
        if experiment == "TestSet":
            show_nudge = True
        return InitializeJivaSerializer.format_jiva(show_nudge)

    async def get_diagnobot_response(
        self, payload: ChatModel.ChatRequestModel, headers: Headers
    ) -> ChatModel.ChatResponseModel:
        """
        This function manages the responses of JivaBot.
        1. Embedding the user prompt.
        2. Retrieving the context from DB.
        3. Augmenting the context with user's prompt.
        4. Synthesizing the final prompt.
        5. Sending the final prompt to LLM.
        6. Returning the response to client.

        @param payload: Request received from client
        @param headers: Headers
        @return: Response to client
        """

        # For 1st time that the chatbot loads, Client sends empty chat_id to initiate the conversation.
        # Upon receiving empty chat_id, we return back with welcome message and a new chat_id.
        if not payload.chat_id:
            return ChatModel.ChatResponseModel(
                data=[ChatTypeMsg.model_validate(Augmentation.CHAT_START_MSG.value)]
            )
        response = await BotResponseFactory.get_bot_response(payload, headers)
        return response

