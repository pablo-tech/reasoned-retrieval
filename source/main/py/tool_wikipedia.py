import time

from langchain.agents import Tool
from langchain import Wikipedia
from langchain.agents.react.base import DocstoreExplorer

from llm_run import ToolRun


class WikipediaExplorer(ToolRun):

    def __init__(self, completion_llm, is_verbose=False):
        super().__init__()
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose
        self.doc_store = DocstoreExplorer(Wikipedia())


class WikipediaSearch(WikipediaExplorer):

    def __init__(self, completion_llm, is_verbose=False):
        super().__init__(completion_llm, is_verbose)

    def run(self, query):
        return self.invoke(query, self.select)

    def select(self, query):
        return self.answer(self.summarize(self.subquery(query)))

    def answer(self, results):
        return [result for result in results]

    def summarize(self, results):
        return [result for result in results]

    def subquery(self, query):
        return eval(self.doc_store.search(query))


class WikipediaLookup(WikipediaExplorer):

    def __init__(self, completion_llm, is_verbose=False):
        super().__init__(completion_llm, is_verbose)

    def run(self, query):
        return self.invoke(query, self.select)

    def select(self, query):
        return self.answer(self.summarize(self.subquery(query)))

    def answer(self, results):
        return [result for result in results]

    def summarize(self, results):
        return [result for result in results]

    def subquery(self, query):
        return eval(self.doc_store.lookup(query))

class EncyclopediaToolFactory():

    def __init__(self, completion_llm, is_verbose=False):
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose

    def wikipedia_tools(self):
        wiki_search = WikipediaSearch(self.completion_llm, self.is_verbose)
        wiki_lookup = WikipediaLookup(self.completion_llm, self.is_verbose)

        return [
          Tool(
              name="Search",
              func=wiki_search.run,
              description="useful to search for the truth"
          ),
          Tool(
              name="Lookup",
              func=wiki_lookup.run,
              description="useful to lookup facts"
          )
        ]
