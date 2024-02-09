from app.service_clients.gemini.gemini_pro import GeminiProServiceClient
from app.models.chat import ChatModel, ChatTypeMsg
from app.routes.end_user.headers import Headers
from app.managers.bots.utils import generate_prompt
from langchain.document_loaders import PyPDFLoader
import ujson


class GeminiAiResponse:

    def __init__(self):
        self.client = GeminiProServiceClient()

    async def get_response(self, payload: ChatModel.ChatRequestModel, headers: Headers):
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
        context = self.get_lab_report_context(lab_report_docs)
        final_prompt = generate_prompt(payload, context)
        print(final_prompt)
        llm_response = self.client.get_response(final_prompt)
        print(llm_response)
        print(type(llm_response))
        return self.generate_response(payload.chat_id, llm_response)

    @staticmethod
    def get_lab_report_documents(payload: ChatModel.ChatRequestModel):
        try:
            print(payload.file_url)
            loader = PyPDFLoader(payload.file_url)
            pages = loader.load()
            return pages
        except Exception as e:
            print(f"An error occurred while loading the PDF: {e}")
            return None

    @staticmethod
    def get_lab_report_context(lab_report_documents):
        final_context = (
            f"Here is the context for lab_report- \n"
            f"User Report - {lab_report_documents}"
        )
        return final_context

    @staticmethod
    def generate_response(
            chat_id: str, llm_response
    ) -> ChatModel.ChatResponseModel:
        """
        Generate response for LLM.
        @param chat_id: Chat id of the conversation
        @param llm_response: Response received from LLM
        @return: Formatted response to be sent to client
        """
        _response = []
        return ChatModel.ChatResponseModel(chat_id=chat_id, data=[ChatTypeMsg(**ujson.loads(llm_response))])



