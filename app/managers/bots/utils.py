from app.constants.constants import Augmentation, JivaChatTypes
from app.models.chat import ChatModel, ChatTypeSkuCard, ChatTypeCallAgent, ChatHistoryModel
from app.caches.jiva import Jiva
import json


def generate_prompt(payload: ChatModel.ChatRequestModel, context=""):
    """
    Generate final prompt for LLM.
    1. Add instructions.
    2. Add context.
    3. Add chat history.
    4. Add user's prompt.
    @param payload: Request received from client
    @param context: Docs fetched from DB as per semantic search.
    @return: A final prompt to be sent to LLM
    """
    final_instructions = Augmentation.INSTRUCTIONS.value
    final_chat_history = ""
    if payload.chat_history and payload.chat_id:
        final_chat_history = generate_chat_memory(payload)
    final_prompt = (
        f"{final_instructions} \n {context} \n {final_chat_history} \n"
        f"Type: {payload.chat_type} \n"
        f"Given above context, please respond against this question - {payload.current_prompt}"
    )
    return final_prompt


def generate_conversation(payload: ChatModel.ChatRequestModel, context=""):
    """
    Generate final prompt for LLM.
    1. Add system instructions.
    2. Add chat history.
    3. Add user's prompt.
    @param payload: Request received from client
    @param context: Docs fetched from DB as per semantic search or lab test report.
    @return: List of messages to be sent to LLM
    """
    system_message = (
        f"{Augmentation.INSTRUCTIONS.value}\n"
        f"Context: {context}\n"
    ) if context else Augmentation.INSTRUCTIONS.value

    conversation = [
        {
            "role": "system",
            "content": system_message
        }
    ]
    for chat in payload.chat_history:
        conversation.append(
            {
                "role": chat.role,
                "content": chat.prompt
            }
        )
    conversation.append({
        "role": "user",
        "content": payload.current_prompt
    })
    return conversation


def generate_chat_memory(payload: ChatModel.ChatRequestModel) -> str:
    """
    Keeping track of chat history is important for a chatbot to be able to provide a human like feel.
    In this function, we format the chat history we get from client to be appended to final_prompt.
    LLM can refer this chat history and modify/enhance its answers accordingly.
    @param payload: Request received from client
    @return: Formatted chat history to be sent to LLM
    """
    final_chat_history = "Here is the chat history - \n"
    for chat in payload.chat_history:
        formed_chat = f"{chat.role}: {chat.prompt}\n"
        final_chat_history += formed_chat + "\n"
    return final_chat_history


async def cache_user_chat_history(payload: ChatModel.ChatRequestModel, serialized_response: ChatModel.ChatResponseModel, context=""):
    """
    Asynchronously caches user chat history, storing information about user interactions and assistant responses.
    @param payload: Request received from client
    @param payload: llm serialized response
    @param context: Additional context information(lab report), used when the chat type is a PDF.
   """
    chat_id = payload.chat_id
    chat_history = []
    cached_user_data = await Jiva.lrange(chat_id)
    user_current_prompt = {"type": JivaChatTypes.ChatTypeMsg.value, "role": "user", "prompt": payload.current_prompt}
    # Redis list doesn't have a support of expiring key, so explicitly setting up expire time
    if not cached_user_data:
        await Jiva.rpush(chat_id, [json.dumps(user_current_prompt)])
        await Jiva.expire(chat_id, Jiva.expiry_time)
    else:
        chat_history.append(user_current_prompt)
    if payload.chat_type == "pdf":
        chat_history.append(
            {
                "type": JivaChatTypes.ChatTypePdf.value,
                "role": "user",
                "prompt": context
            }
        )
    for response in serialized_response.data:
        prompt = (
            response.answer if response.type == JivaChatTypes.ChatTypeMsg.value
            else stringify_sku_card_data(response) if response.type == JivaChatTypes.ChatTypeSkuCard.value
            else stringify_call_agent_data(response) if response.type == JivaChatTypes.ChatTypeCallAgent.value
            else ""
        )
        chat_history.append({
            "type": response.type,
            "role": "assistant",
            "prompt": prompt
        })
    for chat in chat_history:
        await Jiva.rpush(chat_id, [json.dumps(chat)])


def stringify_sku_card_data(response: ChatTypeSkuCard):
    """
    Converts a ChatTypeSkuCard object into a JSON-formatted string.
    @param response: An object representing a response of type 'ChatTypeSkuCard'
    @return: A JSON-formatted string containing the attributes of the ChatTypeSkuCard response.
   """
    return json.dumps({
        "header": response.header,
        "sub_header": response.sub_header,
        "eta": response.eta,
        "price": response.price,
        "sku_id": response.sku_id,
        "cta": response.cta,
        "slug_url": response.slug_url,
        "sku_image": response.sku_image,
        "sku_type": response.sku_type,
        "target_url": response.target_url
    })


def stringify_call_agent_data(response: ChatTypeCallAgent):
    """
    Converts a ChatTypeCallAgent object into a JSON-formatted string.
    @param response: An object representing a response of type 'ChatTypeCallAgent'
    @return: A JSON-formatted string containing the attributes of the ChatTypeCallAgent response.
    """
    return json.dumps({
        "icon": response.icon,
        "header": response.header,
        "sub_header": response.sub_header,
        "target_url": response.target_url
    })


async def get_chat_history(payload: ChatModel.ChatRequestModel, k=8):
    """
    Retrieves the last 'k' chat entries from a given chat ID from cache.
    @param payload: Request received from client
    @return: A JSON-formatted string containing the attributes of the ChatTypeCallAgent response.
    """
    last_k_chats = await Jiva.lrange(payload.chat_id, -k, -1)
    chat_history = []
    for chat in last_k_chats:
        chat_history.append(ChatHistoryModel.model_validate(json.loads(chat)))
    return chat_history
