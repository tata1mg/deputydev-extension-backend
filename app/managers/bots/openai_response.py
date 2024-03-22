from typing import List

import ujson

import app.managers.openai_tools.openai_tools as OpenAITools
from app.constants.constants import Augmentation, JivaChatTypes
from app.constants.error_messages import ErrorMessages
from app.dao.labsConn import LabsConn
from app.dao.openaiembedding import OpenAIEmbeddingsCustom
from app.managers.bots.utils import (
    cache_user_chat_history,
    generate_conversation,
    get_chat_history,
)
from app.models.chat import ChatModel, ChatTypeMsg
from app.routes.end_user.headers import Headers
from app.service_clients.openai.openai import OpenAIServiceClient


class OpenAiResponse:
    def __init__(self):
        self.store = LabsConn().get_store()
        self.client = OpenAIServiceClient()
        self.model = "gpt-4-1106-preview"

    async def get_response(self, payload: ChatModel.ChatRequestModel, headers: Headers):
        payload.chat_history = await get_chat_history(payload)
        contextual_docs = await self.get_diagnostics_documents(payload)
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
        context = self.get_context(contextual_docs, headers.city())
        conversation_messages = generate_conversation(payload, context)
        llm_response = await self.client.get_response(conversation_messages)
        serialized_response = await self.generate_response(payload.chat_id, llm_response)
        await cache_user_chat_history(payload, serialized_response)

        return serialized_response

    async def get_diagnostics_documents(self, payload: ChatModel.ChatRequestModel):
        """
        Fetch lab documents from postgres database.
        contextual_docs: Relevant docs based on user's chat history
        current_prompt_docs: Relevant docs based on user's query
        @param payload: Entire payload received from client
        @return: List of Lab test documents based on user current prompt and user's chat history.
        """
        contextual_docs = []
        current_prompt_docs = []
        if payload.chat_history:
            embedded_prompt: List[float] = self.embedd_prompt(payload)
            # Retrieval
            contextual_docs = await self.store.amax_marginal_relevance_search_by_vector(embedding=embedded_prompt)
        if payload.current_prompt:
            current_prompt_docs = await self.store.amax_marginal_relevance_search_by_vector(
                embedding=self.embedd(payload.current_prompt)
            )
        contextual_docs.extend(current_prompt_docs)
        return contextual_docs

    def embedd_prompt(self, payload: ChatModel.ChatRequestModel, K: int = 6) -> List[float]:
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
            if current_item.type != JivaChatTypes.ChatTypeSkuCard.value:
                result_list.append(current_item.prompt)
        prompt = " ".join(result_list)
        return self.embedd(prompt)

    @staticmethod
    def embedd(prompt):
        embeddings_model = OpenAIEmbeddingsCustom().get_openai_embeddings()
        embedding = embeddings_model.embed_query(prompt)
        return embedding

    def get_context(self, context_documents, city):
        """
        Generate context for LLM. Iterating over docs fetched from DB and constructing relevant context to be
        appended to final_prompt which in turn will be sent to LLM
        @param context_documents: Docs fetched from DB as per semantic search
        @param city: City if user from headers
        @return: Final context generated with use of docs fetched from DB
        """
        user_location = Augmentation.USER_LOCATION.value.format(city)
        final_context = user_location + "Here is the context for diagnostics_query- \n"
        for doc in context_documents:
            formed_context = (
                f"For Test ID {doc.metadata['identifier']}, the Test name is \"{doc.metadata['source']}\" "
                f"and description is as follows \n"
                f"Test description is {doc.page_content} \n"
            )
            final_context += formed_context + "\n"
        return final_context

    @staticmethod
    async def generate_response(chat_id: str, llm_response) -> ChatModel.ChatResponseModel:
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
