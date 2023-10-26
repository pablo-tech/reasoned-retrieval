from langchain.memory import ConversationBufferMemory
from langchain.schema.messages import HumanMessage, AIMessage


class LlmMemory():

    MEMORY_KEY = "chat_history"

    def __init__(self):
        self.memory_buffer = ConversationBufferMemory(memory_key=LlmMemory.MEMORY_KEY,
                                                      return_messages=True)

    def message_exchange(self, human_message, ai_message):
        self.memory_buffer.save_context({"input": human_message}, 
                                        {"output": ai_message})

    def get_history(self):
        return self.memory_buffer.load_memory_variables({})
    
    def __str__(self):
        s = ""
        for message in self.get_history()['chat_history']:
            if isinstance(message, HumanMessage):
                s += "Question: " +  str(message.content) + "\n"
                s += "Thought: I now know the answer." + "\n"
            if isinstance(message, AIMessage):
                content = message.content
                s += "Observation: " + content + "\n"
                s += "Action: Finish" + "[" + content + "]" + "\n"                  
        return s