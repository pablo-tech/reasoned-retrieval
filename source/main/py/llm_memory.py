from langchain.memory import ConversationBufferMemory


class LlmMemory():

    MEMORY_KEY = "chat_history"

    def __init__(self):
        pass

    def conversation_buffer():
        memory_buffer = ConversationBufferMemory(memory_key=LlmMemory.MEMORY_KEY,
                                                return_messages=True)
        return memory_buffer

