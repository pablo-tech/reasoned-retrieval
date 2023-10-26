import os

from langchain import Wikipedia
from langchain.agents import Tool
from langchain.agents.react.base import DocstoreExplorer

from langchain.agents import tool
from langchain.tools.render import render_text_description

from search_tool import SearchAnswer
from math_tool import MathAnswer


class ToolFactory():
    # https://python.langchain.com/docs/modules/agents/tools/custom_tools

    def __init__(self, is_verbose=True):
        self.is_verbose = is_verbose
        self.doc_store = DocstoreExplorer(Wikipedia())

    def tool_summaries(self, tool_set):
        return render_text_description(tool_set)

    def tool_names(self, tool_set):
        return ", ".join([t.name for t in tool_set])

    def basic_tools(self, completion_llm):
        math_tools = self.math_tools(completion_llm)
        # math_tools = load_tools(["llm-math"], completion_llm)
        search_tools = self.search_tools()
        return math_tools + search_tools
        # return load_tools(["serpapi", "llm-math"], completion_llm)

    def math_tools(self, completion_llm):
        return [self.math_engine(completion_llm)]
    
    def math_engine(self, completion_llm):
        math_api = MathAnswer(completion_llm)
        return Tool(
              name="Calculate",
              func=math_api.run,
              description="useful to answer math questions"
        )

    def search_tools(self, completion_llm=None):
        return [self.search_engine()]
    
    def search_engine(self):
        search_api = SearchAnswer()        
        return Tool(
              name="Search",
              func=search_api.run,
              description="useful to answer questions about current events or the current state of the world"
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


