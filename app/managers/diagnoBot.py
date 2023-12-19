from langchain.embeddings import OpenAIEmbeddings

from app.dao.labsConn import LabsConn


class DiagnoBotManager:

    def __init__(self):
        self.store = LabsConn().get_store()

    async def get_diagnobot_response(self, payload):

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

        embeddings_model = OpenAIEmbeddings(openai_api_key="")
        embedding = embeddings_model.embed_query(payload['current_prompt'])
        print(id(self.store))
        docs_with_score = await self.store.amax_marginal_relevance_search_by_vector(embedding=embedding)

        for doc in docs_with_score[::-1]:
            print(doc.page_content)
            print("-------")
        return "pong"
