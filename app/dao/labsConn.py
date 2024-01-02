from langchain.vectorstores.pgvector import PGVector
from commonutils.utils import Singleton
from torpedo import CONFIG
from app.dao.openaiembedding import OpenAIEmbeddingsCustom
from sanic.log import logger

config = CONFIG.config


class LabsConn(metaclass=Singleton):

    def __init__(self):
        conn_str = config.get('DB_CONNECTION').get('CONNECTION_STRING')
        collection_name = config.get('DB_CONNECTION').get('LABS_COLLECTION')
        logger.info("Collection_name: {}".format(collection_name))
        logger.info(conn_str)
        logger.info("Collection_name: {}, Collection_String_type: {}".format(type(collection_name), type(conn_str)))

        embeddings = OpenAIEmbeddingsCustom().get_openai_embeddings()
        store = PGVector(
            collection_name=collection_name,
            collection_metadata={"email": "vishal.khare@1mg.com"},
            connection_string=conn_str,
            embedding_function=embeddings
        )
        self.store = store

    def get_store(self):
        return self.store
