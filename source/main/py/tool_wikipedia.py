from langchain.agents import Tool
from langchain import Wikipedia
from langchain.agents.react.base import DocstoreExplorer

from llm_run import ToolRun

import wikipedia


class WikipediaExplorer(ToolRun):

    def __init__(self, completion_llm, is_verbose=False):
        super().__init__()
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose
        self.doc_store = DocstoreExplorer(Wikipedia())


class WikipediaDocstoreSearch(WikipediaExplorer):

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
        # TODO Could not find [Rodriguez]. Similar: ['Rodriguez', 'Alex Rodriguez', 'Iván Rodríguez', 'Adam Rodriguez', 'Michelle Rodriguez', 'Robert Rodriguez', 'Eduardo Rodríguez', 'Michaela Jaé Rodriguez', 'Georgina Rodríguez', 'Gina Rodriguez']
        return [str(self.doc_store.search(query))]


class WikipediaDocstoreLookup(WikipediaExplorer):

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
        return [str(self.doc_store.lookup(query))]
    

class WikipediaWrapper(ToolRun):

    def __init__(self, completion_llm, is_verbose=False):
        super().__init__()
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose
        self.doc_store = wikipedia


class WikipediaSearch(WikipediaWrapper):

    def __init__(self, completion_llm, is_verbose=False):
        super().__init__(completion_llm, is_verbose)

    def run(self, query):
        return self.invoke(query, self.select)

    def select(self, query):
        return self.answer(self.summarize(self.subquery(query)))

    def answer(self, results):
        return [result for result in results]

    def summarize(self, results, k=5, n=5):
        snippet = []
        for result in results:
          try:
            snippet.append(self.doc_store.summary(result,
                                                  sentences=n))
          except Exception as e:
            # print("SEARCH_SUMMARIZE_ERROR=" + str(e))
            pass
          if len(snippet) >= k:
            return snippet
        return snippet

    def subquery(self, query):
        try:
          return self.doc_store.search(query)
        except Exception as e:
          # print("SEARCH_SUBQUERY_ERROR=" + str(e))
          return [str(e)]


class WikipediaLookup(WikipediaWrapper):

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
        # TODO Could not find [Rodriguez]. Similar: ['Rodriguez', 'Alex Rodriguez', 'Iván Rodríguez', 'Adam Rodriguez', 'Michelle Rodriguez', 'Robert Rodriguez', 'Eduardo Rodríguez', 'Michaela Jaé Rodriguez', 'Georgina Rodríguez', 'Gina Rodriguez']
        response = []
        try:
          response = self.doc_store.page(query).content
        except Exception as e:
          # print("LOOKUP_SUBQUERY_ERROR=" + str(e))
          response = str(e)
        return ["".join(response)]


class EncyclopediaToolFactory():

    def __init__(self, completion_llm, is_verbose=False):
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose

    def wikipedia_tools(self):
        wiki_search = WikipediaSearch(self.completion_llm, self.is_verbose)
        wiki_lookup = WikipediaLookup(self.completion_llm, self.is_verbose)
        # wiki_search = WikipediaDocstoreSearch(self.completion_llm, self.is_verbose)
        # wiki_lookup = WikipediaDocstoreLookup(self.completion_llm, self.is_verbose)

        return [
          Tool(
              name="Search",
              func=wiki_search.run,
              description="useful to search for the truth"
          ),
          Tool(
              name="Lookup",
              func=wiki_lookup.run,
              description="useful to lookup named entity facts"
          )
        ]
