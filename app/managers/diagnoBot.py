from typing import List
from app.dao.openaiembedding import OpenAIEmbeddingsCustom
from app.dao.labsConn import LabsConn
from app.constants.constants import Augmentation
from app.constants.error_messages import ErrorMessages
from app.models.chat import ChatRequestModel


class DiagnoBotManager:
    def __init__(self):
        self.store = LabsConn().get_store()

    async def get_diagnobot_response(self, payload: ChatRequestModel):

        """
        1. Embedd user prompt.
        2. Check for chat_id
        3. If chat_id is null, Initiate a fresh conversation with LLM i.e. no chat_history
        4. If chat_id is not null, Along with context + prompt also send chat_history to LLM.
        5. Get response from LLM and send to user.

        5a - Ingest all labs data vectorized in PostgresDB
        5b - Also implement a websocket API and stream the response to client.

        @param payload:
        @return:
        """
        # Embedding
        embedded_prompt = self.embedd_prompt(payload.current_prompt)
        # Retrieval
        docs = await self.store.amax_marginal_relevance_search_by_vector(
            embedding=embedded_prompt
        )
        if not docs:
            return ErrorMessages.RETRIEVAL_FAIL_MSG.value
        # Augmentation
        final_prompt = self.generate_final_prompt(payload, docs)
        print(final_prompt)
        #
        #
        # for doc in docs[::-1]:
        #     print(doc)
        #     print("-------")
        return "pong"

    @staticmethod
    def embedd_prompt(prompt) -> List[float]:
        embeddings_model = OpenAIEmbeddingsCustom().get_openai_embeddings()
        embedding = embeddings_model.embed_query(prompt)
        return embedding

    @staticmethod
    def generate_final_prompt(payload, context) -> str:
        final_instructions = Augmentation.INSTRUCTIONS.value
        final_context = DiagnoBotManager.generate_context(context)
        final_chat_history = ""
        if payload.chat_history and payload.chat_id:
            final_chat_history = DiagnoBotManager.generate_chat_memory(payload)
        final_prompt = (
            f"{final_instructions} \n {final_context} \n {final_chat_history} \n Given above context, "
            f"please respond against this question - {payload.current_prompt}"
        )
        return final_prompt

    @staticmethod
    def generate_context(context) -> str:
        final_context = "Here is the context - \n"
        for doc in context:
            formed_context = (
                f"For Test ID {doc.metadata['identifier']} the Test name is \"{doc.metadata['source']}\" and description is as follows \n"
                f"Test description is {doc.page_content} \n"
            )
            final_context += formed_context + "\n"
        return final_context

    @staticmethod
    def generate_chat_memory(payload) -> str:
        final_chat_history = "Here is the chat history - \n"
        for chat in payload.chat_history:
            formed_chat = f"{chat.role}: {chat.prompt}\n"
            final_chat_history += formed_chat + "\n"
        return final_chat_history
