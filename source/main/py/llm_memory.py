from langchain.memory import ConversationBufferMemory
from langchain.schema.messages import HumanMessage, AIMessage


class LlmMemory():

    MEMORY_KEY = "chat_history"

    def __init__(self, human_name="Human: ", ai_name="AI: "):
        self.human_key = human_name
        self.ai_name = ai_name

        self.memory_buffer = ConversationBufferMemory(memory_key=LlmMemory.MEMORY_KEY,
                                                      return_messages=True)

    # def conversation_buffer():
    #     memory_buffer = ConversationBufferMemory(memory_key=LlmMemory.MEMORY_KEY,
    #                                             return_messages=True)
    #     return memory_buffer 

    def message_exchange(self, human_message, ai_message):
        self.memory_buffer.save_context({"input": human_message}, 
                                        {"output": ai_message})

    def get_history(self):
        return self.memory_buffer.load_memory_variables({})
    
    def __str__(self):
        s = ""
        for message in self.get_history():
            if isinstance(message, HumanMessage):
                s += self.human_name +":" + str(message.content)
            if isinstance(message, AIMessage):
                s += self.ai_name +":" + str(message.content)
        return s