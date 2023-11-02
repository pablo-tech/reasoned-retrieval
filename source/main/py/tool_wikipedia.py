from langchain.agents import Tool
from langchain import Wikipedia
from langchain.agents.react.base import DocstoreExplorer


class EncyclopediaToolFactory():

    def __init__(self, is_verbose=False):
        self.is_verbose = is_verbose

    def wikipedia_tools(self, completion_llm=None):
        doc_store = DocstoreExplorer(Wikipedia())
        return [
          Tool(
              name="Search",
              func=doc_store.search,
              description="useful to search for the truth"
          ),
          Tool(
              name="Lookup",
              func=doc_store.lookup,
              description="useful to lookup facts"
          )
        ]
