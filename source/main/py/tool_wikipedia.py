from langchain.agents import Tool

import wikipedia    

from helper_select import SelectHelper


class WikipediaRetriever(SelectHelper):
    # https://pypi.org/project/wikipedia/

    def __init__(self, completion_llm, is_verbose=False):
        super().__init__("WIKIPEDIA", completion_llm, is_verbose)
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose
        self.doc_store = wikipedia


class WikipediaSearchReader(WikipediaRetriever):

    def __init__(self, completion_llm, is_verbose=False):
        super().__init__(completion_llm, is_verbose)

    def run(self, tool_input, user_query=""):
        return self.invoke(tool_input, self.select)

    def select(self, query):
        results = self.subquery(query)
        return self.answer(self.summarize(results, query), query)

    def subquery(self, query, k=5, n=5):
        results = []
        try:
          results = self.doc_store.search(query)
        except Exception as e:
          # print("SEARCH_SUBQUERY_ERROR=" + str(e))
          return [str(e)]
        snippets = []
        for result in results:
          try:
            snippets.append(self.doc_store.summary(result,
                                                   sentences=n))
          except Exception as e:
            # print("SEARCH_SUMMARIZE_ERROR=" + str(e))
            pass
          if len(snippets) >= k:
            return snippets
        return snippets


class WikipediaLookupReader(WikipediaRetriever):

    def __init__(self, completion_llm, is_verbose=False):
        super().__init__(completion_llm, is_verbose)

    def run(self, tool_input, user_query=""):
        return self.invoke(tool_input, self.select)

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

    def get_tools(self):
        search = WikipediaSearchReader(self.completion_llm, self.is_verbose)
        lookup = WikipediaLookupReader(self.completion_llm, self.is_verbose)

        return [
          Tool(
              name="Search",
              func=search.run,
              description="useful to search for the truth"
          ),
          Tool(
              name="Lookup",
              func=lookup.run,
              description="useful to lookup named entity facts"
          )
        ]
