

from langchain.agents import Tool

from llm_select import ToolSelect


class ConversationAnswer(ToolSelect):

    def __init__(self, completion_llm, is_verbose):
        super().__init__("CONVERSATION", completion_llm, is_verbose)

    def run(self, tool_input):
        return self.invoke(tool_input, self.select)

    def select(self, query):
        results = self.subquery(query)
        return self.answer(self.summarize(results, query), query)
    
    def subquery(self, txt):
        return txt


class ConversationToolFactory():

    def __init__(self, completion_llm, is_verbose=False):
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose

    def get_tools(self):
        api = ConversationAnswer(self.completion_llm, self.is_verbose)        
        return [
            Tool(
              name="Message",
              func=api.run,
              description="useful to send a message to the user"
        )]