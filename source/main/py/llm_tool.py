import os

from langchain import OpenAI, Wikipedia
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
from langchain.agents.react.base import DocstoreExplorer

from langchain.agents import load_tools
from langchain.tools.render import render_text_description
from langchain.utilities import SerpAPIWrapper


class ToolFactory():

    def __init__(self):
        ## Search engine api
        # https://serpapi.com/dashboard
        os.environ['SERPAPI_API_KEY'] = '2c24c5acccd4ab1f8644348773293cac5aa6907314eb0685ab2d8ad3d75e528d'
        self.search_api = SerpAPIWrapper()
        ## Document store
        self.doc_store = DocstoreExplorer(Wikipedia())

    def tool_summaries(self, tool_set):
        return render_text_description(tool_set)

    def tool_names(self, tool_set):
        return ", ".join([t.name for t in tool_set])

    def basic_tools(self, completion_llm):
        return load_tools(["serpapi", "llm-math"], completion_llm)

    def search_tools(self, completion_llm=None):
        return [
          Tool(
              name="Search",
              func=self.search_api.run,
              description="useful for when you need to answer questions about current events or the current state of the world"
          ),
        ]

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