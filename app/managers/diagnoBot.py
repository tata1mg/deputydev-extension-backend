from typing import List

import ujson
from openai.types.chat import ChatCompletionMessage

from app.dao.openaiembedding import OpenAIEmbeddingsCustom
from app.dao.labsConn import LabsConn
from app.constants.constants import Augmentation
from app.constants.error_messages import ErrorMessages
from app.models.chat import ChatModel, ChatTypeMsg
from app.service_clients.openai.openai import OpenAIServiceClient
import app.managers.openai_tools.openai_tools as OpenAITools


class DiagnoBotManager:
    def __init__(self):
        self.store = LabsConn().get_store()

    async def get_diagnobot_response(
        self, payload: ChatModel.ChatRequestModel
    ) -> ChatModel.ChatResponseModel:
        """
        This function manages the responses of DiagnoBot.
        1. Embedding the user prompt.
        2. Retrieving the context from DB.
        3. Augmenting the context with user's prompt.
        4. Synthesizing the final prompt.
        5. Sending the final prompt to LLM.
        6. Returning the response to client.

        @param payload: Request received from client
        @return: Response to client
        """

        # For 1st time that the chatbot loads, Client sends empty chat_id to initiate the conversation.
        # Upon receiving empty chat_id, we return back with welcome message and a new chat_id.
        if not payload.chat_id:
            return ChatModel.ChatResponseModel(
                data=[ChatTypeMsg(**Augmentation.CHAT_START_MSG.value)]
            )

        # Embedding
        embedded_prompt: List[float] = self.embedd_prompt(payload)

        # Retrieval
        docs = await self.store.amax_marginal_relevance_search_by_vector(
            embedding=embedded_prompt
        )
        if not docs:
            return ChatModel.ChatResponseModel(
                chat_id=payload.chat_id,
                data=[
                    ChatTypeMsg(
                        **{
                            "answer": ErrorMessages.RETRIEVAL_FAIL_MSG.value,
                        }
                    )
                ],
            )
        # Augmentation
        final_prompt: str = self.generate_final_prompt(payload, docs)

        # Generation/Synthesis
        llm_response: ChatCompletionMessage = (
            OpenAIServiceClient().get_diagnobot_response(final_prompt=final_prompt)
        )

        # Serialization
        return await self.generate_response(payload.chat_id, llm_response)

    @staticmethod
    def embedd_prompt(payload: ChatModel.ChatRequestModel, K: int = 3) -> List[float]:
        """
        Create vector embeddings for a given prompt.
        @param K: Number of historical messages to factor in while creating a prompt.
        @param payload: Entire payload received from client
        @return: Vector embedding equivalent of chat's history and user's prompt.
        """
        embeddings_model = OpenAIEmbeddingsCustom().get_openai_embeddings()
        chat_history = payload.chat_history
        result_list = []
        for i in range(len(chat_history) - 1, max(-1, len(chat_history) - K - 1), -1):
            current_item = chat_history[i]
            result_list.append(current_item.prompt)
        result_list.append(payload.current_prompt)
        prompt = " ".join(result_list)
        embedding = embeddings_model.embed_query(prompt)
        return embedding

    @staticmethod
    def generate_final_prompt(payload, context) -> str:
        """
        Generate final prompt for LLM.
        1. Add instructions.
        2. Add context.
        3. Add chat history.
        4. Add user's prompt.
        @param payload: Request received from client
        @param context: Docs fetched from DB as per semantic search.
        @return: A final prompt to be sent to LLM
        """
        final_instructions = Augmentation.INSTRUCTIONS.value
        final_context = DiagnoBotManager.generate_context(context)
        final_chat_history = ""
        # TODO : Extract user's current location from headers and inject it here as part of final prompt.
        if payload.chat_history and payload.chat_id:
            final_chat_history = DiagnoBotManager.generate_chat_memory(payload)
        final_prompt = (
            f"{final_instructions} \n {final_context} \n {final_chat_history} \n Given above context, "
            f"please respond against this question - {payload.current_prompt}"
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
            _response.extend(await func(llm_response.tool_calls[0].function.arguments))
        return ChatModel.ChatResponseModel(chat_id=chat_id, data=_response)
