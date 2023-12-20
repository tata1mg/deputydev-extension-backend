from enum import Enum

from torpedo.common_utils import CONFIG, json_file_to_dict

X_SHARED_CONTEXT='X-SHARED-CONTEXT'
ENVIRONMENT=CONFIG.config['ENVIRONMENT']


class ListenerEventTypes(Enum):
    AFTER_SERVER_START="after_server_start"
    BEFORE_SERVER_START="before_server_start"
    BEFORE_SERVER_STOP="before_server_stop"
    AFTER_SERVER_STOP="after_server_stop"


class ExtendedEnum(Enum):
    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class Augmentation(Enum):
    INSTRUCTIONS = """
    You are a medical diagnostic agent capable of answering questions based of context given to you designed to output in JSON.
    Now consider the following TypeScript Interface for the JSON schema:
    interface Message {
        answer: string;
        advice: string;
        followup: string;
    }
    Apart from answering user questions, please follow following guardrails-
    1. Always ask users to consult with their doctors for any health checkup.
    2. If user prompt and context are unrelated, just say something like - "I don't understand what you are saying. 
    I am a medical diagnostic agent and my knowledge is limited to this domain only."
    3. If user prompt and context are related, then try to answer the user prompt based on the context given.
    4. Given chat history try to answer the question that requires chat's historical context.
    related queries.
    """
