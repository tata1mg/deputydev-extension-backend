import ujson
from langchain.document_loaders import PyPDFLoader

from app.backend_common.service_clients.gemini.gemini_pro import GeminiProServiceClient
from app.common.constants.error_messages import ErrorMessages
from app.common.utils.headers import Headers
from app.main.blueprints.jiva.constants.prompts.v1.prompts import USER_LOCATION
from app.main.blueprints.jiva.models.chat import ChatModel, ChatTypeMsg
from app.main.blueprints.jiva.services.bots.utils import (
    cache_user_chat_history,
    generate_prompt,
    get_chat_history,
)


class GeminiAiResponse:
    def __init__(self):
        self.client = GeminiProServiceClient()

    async def get_response(self, payload: ChatModel.ChatRequestModel, headers: Headers):
        payload.chat_history = await get_chat_history(payload)
        lab_report_docs = self.get_lab_report_documents(payload)
        if not lab_report_docs:
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
        context = self.get_context(lab_report_docs, headers.city())
        final_prompt = generate_prompt(payload, context)
        llm_response = self.client.get_response(final_prompt)
        serialized_response = self.generate_response(payload.chat_id, llm_response)
        await cache_user_chat_history(payload, serialized_response, context)
        return serialized_response

    @staticmethod
    def get_lab_report_documents(payload: ChatModel.ChatRequestModel):
        try:
            loader = PyPDFLoader(payload.file_url)
            pages = loader.load()
            return pages
        except Exception as e:
            print(f"An error occurred while loading the PDF: {e}")
            return None

    @staticmethod
    def get_context(lab_report_documents, city):
        user_location = USER_LOCATION.format(city)
        final_context = f"{user_location} \n" f"Here is the page wise context for lab_report- \n"
        for doc in lab_report_documents:
            formed_context = f"For Page {doc.metadata['page']} \n" f"Content is {doc.page_content} \n"
            final_context += formed_context + "\n"
        return final_context

    @staticmethod
    def generate_response(chat_id: str, llm_response) -> ChatModel.ChatResponseModel:
        """
        Generate response for LLM.
        @param chat_id: Chat id of the conversation
        @param llm_response: Response received from LLM
        @return: Formatted response to be sent to client
        """
        return ChatModel.ChatResponseModel(chat_id=chat_id, data=[ChatTypeMsg(**ujson.loads(llm_response))])
