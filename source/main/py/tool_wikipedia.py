from langchain.agents import Tool
from langchain import Wikipedia
from langchain.agents.react.base import DocstoreExplorer


class EncyclopediaTools():

    def wikipedia_tools(completion_llm=None):
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
