

from langchain.agents import Tool

from helper_select import SelectHelper


class ConversationRetriever(SelectHelper):

    def __init__(self, completion_llm, is_verbose):
        super().__init__("CONVERSATION", completion_llm, is_verbose)

    def subquery(self, txt):
        return txt


class ConversationReader(ConversationRetriever):

    def __init__(self, completion_llm, is_verbose):
        super().__init__(completion_llm, is_verbose)

    def run(self, tool_input):
        return self.invoke(tool_input, self.select)

    def select(self, query):
        results = self.subquery(query)
        return self.answer(self.summarize(results, query), query)
    

class ConversationToolFactory():

    def __init__(self, completion_llm, is_verbose=False):
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose

    def get_tools(self):
        api = ConversationReader(self.completion_llm, self.is_verbose)        
        return [
            Tool(
              name="Message",
              func=api.run,
              description="useful to send a message to the user"
        )]