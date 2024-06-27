from commonutils.utils import Singleton
from langchain.embeddings import OpenAIEmbeddings
from torpedo import CONFIG

config = CONFIG.config


class OpenAIEmbeddingsCustom(metaclass=Singleton):
    def __init__(self, openai_api_key: str = config.get("OPENAI_KEY")):
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)

    def get_openai_embeddings(self):
        return self.embeddings
