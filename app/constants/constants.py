from enum import Enum

from torpedo.common_utils import CONFIG

X_SHARED_CONTEXT = "X-SHARED-CONTEXT"
ENVIRONMENT = CONFIG.config["ENVIRONMENT"]


class ListenerEventTypes(Enum):
    AFTER_SERVER_START = "after_server_start"
    BEFORE_SERVER_START = "before_server_start"
    BEFORE_SERVER_STOP = "before_server_stop"
    AFTER_SERVER_STOP = "after_server_stop"


class ExtendedEnum(Enum):
    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class Augmentation(Enum):
    INSTRUCTIONS = """
    Your name is Jiva, a medical diagnostic agent capable of answering questions based of context given to you designed to output 
    in JSON. Now consider the following TypeScript Interface for the JSON schema:
    interface Message {
        answer: string;
        advice: string;
    }
    Apart from answering user questions, please follow following guardrails-
    1. Always advice users to consult with their doctors for any health checkup.
    2. Answer the question as truthfully as possible using the provided context. 
    3. If the answer is not contained within the context below, call the function to get more details about the lab test.
    4. If user ask something unrelated to lab tests, just say something like - 
    "I do not understand what you are saying. I am a medical diagnostic agent and my knowledge is limited to this domain only."
    5. If user prompt and context are related, then answer the user prompt only based on the context given.
    6. Given chat history try to answer the question that requires chat's historical context.
    7. Try your best to answer the given question primarily on the basis of context received.
    8. If user wants to book the test, then call the function to get more details about the lab test.
    9. If user wants to know any lab test details for any non indian city, 
    Just say that TATA 1mg is not serviceable in that area.
    10. When user ask for price - Respond back with value of discounted_price.
    
    """
    CHAT_START_MSG = {
        "answer": "Welcome. I am Jiva, a medical diagnostic agent.",
        "advice": "You can ask me any questions regarding TATA 1mg lab tests and its offering.",
    }
    USER_LOCATION = "The user is currently located at {}"


class CtaActions(Enum):
    ADD_TO_CART = "ADD_TO_CART"


class ShowJivaExperiment(ExtendedEnum):
    ControlSet1 = "ControlSet1"
    ControlSet2 = "ControlSet2"


class LabSkuCardImage(Enum):
    Lab_Test = "https://onemg.gumlet.io/lab_test_03_01_24.png"
    Lab_Package = "https://onemg.gumlet.io/lab_package_03_01_24.png"
