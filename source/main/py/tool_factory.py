import os

from langchain import Wikipedia
from langchain.agents import Tool
from langchain.agents.react.base import DocstoreExplorer

from langchain.agents import tool
from langchain.tools.render import render_text_description

from tool_search import SerpSearchFactory
from tool_math import MathAnswer
from tool_conversation import ConversationAnswer

class ToolFactory():
    # https://python.langchain.com/docs/modules/agents/tools/custom_tools

    def __init__(self, is_verbose=True):
        self.is_verbose = is_verbose
        self.doc_store = DocstoreExplorer(Wikipedia())

    def tool_summaries(cls, tool_set):
        return render_text_description(tool_set)

    def tool_names(cls, tool_set):
        return ", ".join([t.name for t in tool_set])

    def basic_tools(self, completion_llm):
        math_tools = [self.math_tool(completion_llm)]
        search_tools = self.search_tools(completion_llm)
        conversation_tools = self.conversation_tools()
        return math_tools + search_tools + conversation_tools
    
    def search_tools(self, completion_llm):
        return [SerpSearchFactory.search_tool(completion_llm)]

    def math_tool(self, completion_llm):
        math_api = MathAnswer(completion_llm) 
        return Tool(
              name="Calculate",
              func=math_api.run,
              description="useful to answer math questions"
        )
        
    def conversation_tools(self, completion_llm=None):
        return [self.conversation_engine()]
    
    def conversation_engine(self):
        conversation_api = ConversationAnswer()        
        return Tool(
              name="Message",
              func=conversation_api.send_message,
              description="useful to send a message to the user"
        )
    
    def wikipedia_tools(self, completion_llm=None):
        return [
          Tool(
              name="Search",
              func=self.doc_store.search,
              description="useful to search for the truth"
          ),
          Tool(
              name="Lookup",
              func=self.doc_store.lookup,
              description="useful to lookup facts"
          )
        ]
    
    @tool
    def get_word_length(word):
        """Returns the length of a word."""
        return len(word)

    def string_tools():
        return [ToolFactory.get_word_length]


