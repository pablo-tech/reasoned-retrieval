

from langchain.agents import Tool


class ConversationAnswer():

    def __init__(self):
        pass

    def send_message(self, txt):
        return txt
    

class ConversationFactory():

    def conversation_tools(self, completion_llm):
        conversation_api = ConversationAnswer()        
        return [
            Tool(
              name="Message",
              func=conversation_api.send_message,
              description="useful to send a message to the user"
        )]