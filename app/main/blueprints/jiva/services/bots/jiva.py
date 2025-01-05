from typing import List

import ujson
from openai.types.chat import ChatCompletionMessage

import app.main.blueprints.jiva.services.openai.openai_tools as OpenAITools
from app.backend_common.service_clients import OpenAIServiceClient
from app.backend_common.services.openai.openaiembedding import OpenAIEmbeddingsCustom
from app.backend_common.utils.app_utils import get_ab_experiment_set
from app.common.constants.error_messages import ErrorMessages
from app.common.utils.headers import Headers
from app.main.blueprints.jiva.constants.prompts.v1.prompts import (
    CHAT_START_MSG,
    INSTRUCTIONS,
    USER_LOCATION,
)
from app.main.blueprints.jiva.models.chat import ChatModel, ChatTypeMsg
from app.main.blueprints.jiva.pre_posessors.initialize_jiva_serializer import (
    InitializeJivaSerializer,
)
from app.main.blueprints.jiva.services.embeddings.labsConn import LabsConn


class JivaManager:
    def __init__(self):
        self.store = LabsConn().get_store()

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
            return ChatModel.ChatResponseModel(data=[ChatTypeMsg.model_validate(CHAT_START_MSG)])

        # Embedding
        contextual_docs = []
        current_prompt_docs = []
        if payload.chat_history:
            embedded_prompt: List[float] = self.embedd_prompt(payload)
            # Retrieval
            contextual_docs = await self.store.amax_marginal_relevance_search_by_vector(embedding=embedded_prompt)
        if payload.current_prompt:
            current_prompt_docs = await self.store.amax_marginal_relevance_search_by_vector(
                embedding=JivaManager.embedd(payload.current_prompt)
            )
        # Merging contextual docs with docs fetched against current prompt.
        contextual_docs.extend(current_prompt_docs)

        # contextual_docs = await self.retrieve_docs_from_prompt(payload)
        if not contextual_docs:
            return ChatModel.ChatResponseModel(
                chat_id=payload.chat_id,
                data=[
                    ChatTypeMsg.model_validate(
                        {
                            "answer": ErrorMessages.RETRIEVAL_FAIL_MSG.value,
                        }
                    )
                ],
            )
        # Augmentation
        final_prompt: str = self.generate_final_prompt(payload, contextual_docs, headers.city())

        # Generation/Synthesis
        llm_response: ChatCompletionMessage = await OpenAIServiceClient().get_diagnobot_response(
            final_prompt=final_prompt
        )

        # Serialization
        return await self.generate_response(payload.chat_id, llm_response)

    @staticmethod
    def embedd_prompt(payload: ChatModel.ChatRequestModel, K: int = 6) -> List[float]:
        """
        Create vector embeddings for a given prompt.
        @param K: Number of historical messages to factor in while creating a prompt.
        @param payload: Entire payload received from client
        @return: Vector embedding equivalent of chat's history and user's prompt.
        """

        chat_history = payload.chat_history
        result_list = []
        for i in range(len(chat_history) - 1, max(-1, len(chat_history) - K - 1), -1):
            current_item = chat_history[i]
            result_list.append(current_item.prompt)
        prompt = " ".join(result_list)
        return JivaManager.embedd(prompt)

    @staticmethod
    def embedd(prompt):
        embeddings_model = OpenAIEmbeddingsCustom().get_openai_embeddings()
        embedding = embeddings_model.embed_query(prompt)
        return embedding

    @staticmethod
    def generate_final_prompt(payload, context, city) -> str:
        """
        Generate final prompt for LLM.
        1. Add instructions.
        2. Add context.
        3. Add chat history.
        4. Add user's prompt.
        @param payload: Request received from client
        @param context: Docs fetched from DB as per semantic search.
        @param city: User's location
        @return: A final prompt to be sent to LLM
        """
        final_instructions = INSTRUCTIONS
        final_context = JivaManager.generate_context(context)
        final_chat_history = ""
        # city = "Delhi"  # Harcoded this for now
        user_location = USER_LOCATION.format(city)
        if payload.chat_history and payload.chat_id:
            final_chat_history = JivaManager.generate_chat_memory(payload)
        final_prompt = (
            f"{final_instructions} \n {user_location} \n {final_context} \n {final_chat_history} \n"
            f"Given above context, please respond against this question - {payload.current_prompts}"
        )
        return final_prompt

    @staticmethod
    def generate_context(context) -> str:
        """
        Generate context for LLM. Iterating over docs fetched from DB and constructing relevant context to be
        appended to final_prompt which in turn will be sent to LLM
        @param context: Docs fetched from DB as per semantic search
        @return: Final context generated with use of docs fetched from DB
        """
        final_context = "Here is the context - \n"
        for doc in context:
            formed_context = (
                f"For Test ID {doc.metadata['identifier']}, the Test name is \"{doc.metadata['source']}\" "
                f"and description is as follows \n"
                f"Test description is {doc.page_content} \n"
            )
            final_context += formed_context + "\n"
        return final_context

    @staticmethod
    def generate_chat_memory(payload) -> str:
        """
        Keeping track of chat history is important for a chatbot to be able to provide a human like feel.
        In this function, we format the chat history we get from client to be appended to final_prompt.
        LLM can refer this chat history and modify/enhance its answers accordingly.
        @param payload: Request received from client
        @return: Formatted chat history to be sent to LLM
        """
        final_chat_history = "Here is the chat history - \n"
        for chat in payload.chat_history:
            formed_chat = f"{chat.role}: {chat.prompt}\n"
            final_chat_history += formed_chat + "\n"
        return final_chat_history

    @staticmethod
    async def generate_response(chat_id: str, llm_response: ChatCompletionMessage) -> ChatModel.ChatResponseModel:
        """
        Generate response for LLM.
        @param chat_id: Chat id of the conversation
        @param llm_response: Response received from LLM
        @return: Formatted response to be sent to client
        """
        _response = []
        if llm_response.content:
            _response.append(ChatTypeMsg(**ujson.loads(llm_response.content)))
        if llm_response.tool_calls:
            func = getattr(OpenAITools, llm_response.tool_calls[0].function.name)
            _response.extend(await func(**ujson.loads(llm_response.tool_calls[0].function.arguments)))
        return ChatModel.ChatResponseModel(chat_id=chat_id, data=_response)
