from langchain.vectorstores.pgvector import PGVector
from commonutils.utils import Singleton
from torpedo import CONFIG
from app.dao.openaiembedding import OpenAIEmbeddingsCustom

config = CONFIG.config


class LabsConn():

    def __init__(self):
        conn_str = config.get("DB_CONNECTION").get("CONNECTION_STRING")
        collection_name = config.get("DB_CONNECTION").get("LABS_COLLECTION")
        embeddings = OpenAIEmbeddingsCustom().get_openai_embeddings()
        self.store = PGVector(
            collection_name=collection_name,
            collection_metadata={"email": "vishal.khare@1mg.com"},
            connection_string=conn_str,
            embedding_function=embeddings,
            engine_args={
                "pool_pre_ping": True,
                "echo_pool": True,
                "pool_size": 10,
                "max_overflow": 5

            }
        )

    def get_store(self):
        return self.store
