from app.constants.constants import Augmentation
def generate_prompt(payload, context=""):
    """
    Generate final prompt for LLM.
    1. Add instructions.
    2. Add context.
    3. Add chat history.
    4. Add user's prompt.
    @param payload: Request received from client
    @param context: Docs fetched from DB as per semantic search.
    @param city: User's location
    @return: A final prompt to be sent to LLM
    """
    final_instructions = Augmentation.INSTRUCTIONS.value
    # final_context = JivaManager.generate_context(context)
    final_chat_history = ""
    # city = "Delhi"  # Harcoded this for now
    # user_location = Augmentation.USER_LOCATION.value.format(city)
    if payload.chat_history and payload.chat_id:
        final_chat_history = generate_chat_memory(payload)
    final_prompt = (
        f"{final_instructions} \n {context} \n {final_chat_history} \n"
        f"Type: {payload.chat_type} \n"
        f"Given above context, please respond against this question - {payload.current_prompt}"
    )
    return final_prompt


def generate_chat_memory(payload) -> str:
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

