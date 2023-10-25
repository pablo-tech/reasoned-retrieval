import os

from langchain import Wikipedia
from langchain.agents import Tool
from langchain.agents.react.base import DocstoreExplorer

from langchain.agents import tool
from langchain.agents import load_tools
from langchain.tools.render import render_text_description

from search_tool import SearchAnswer


class ToolFactory():

    def __init__(self):
        ## Search engine api
        self.search_api = SearchAnswer()
        ## Document store
        self.doc_store = DocstoreExplorer(Wikipedia())

    def tool_summaries(self, tool_set):
        return render_text_description(tool_set)

    def tool_names(self, tool_set):
        return ", ".join([t.name for t in tool_set])

    def basic_tools(self, completion_llm):
        math_tools = load_tools(["llm-math"], completion_llm)
        search_tools = self.search_tools()
        return math_tools + search_tools
        # return load_tools(["serpapi", "llm-math"], completion_llm)

    def search_tools(self, completion_llm=None):
        return [self.search_engine()]
    
    def search_engine(self):
        return Tool(
              name="Search",
              func=self.search_api.run,
              description="useful for when you need to answer questions about current events or the current state of the world"
        )

    def wikipedia_tools(self, completion_llm=None):
        return [
          Tool(
              name="Search",
              func=self.doc_store.search,
              description="useful for when you need to ask with search"
          ),
          Tool(
              name="Lookup",
              func=self.doc_store.lookup,
              description="useful for when you need to ask with lookup"
          )
        ]
    
    @tool
    def get_word_length(word):
        """Returns the length of a word."""
        return len(word)

    def string_tools():
        return [ToolFactory.get_word_length]


