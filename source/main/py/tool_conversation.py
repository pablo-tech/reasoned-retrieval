

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

    def run(self, tool_input="", user_query="", query_filter={}):
        return self.invoke(tool_input, query_filter, self.select)

    def select(self, query_txt, query_filter):
        results = self.subquery(query_txt)
        return self.answer(self.summarize(results, query_txt), query_txt)
    

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