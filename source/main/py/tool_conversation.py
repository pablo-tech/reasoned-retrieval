

from langchain.agents import Tool


class ConversationAnswer():

    def __init__(self):
        pass

    def send_message(self, txt):
        return txt
    

class ConversationToolFactory():

    def __init__(self, completion_llm, is_verbose=False):
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose

    def get_tools(self):
        conversation_api = ConversationAnswer()        
        return [
            Tool(
              name="Message",
              func=conversation_api.send_message,
              description="useful to send a message to the user"
        )]