from langchain.agents import Tool

from llm_run import ToolRun

    

class HotpotDataset(ToolRun):
    # https://pypi.org/project/wikipedia/

    def __init__(self, completion_llm, is_verbose=False):
        super().__init__()
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose
        self.doc_store = wikipedia


class HotpotExample(HotpotDataset):

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



class EncyclopediaToolFactory():

    def __init__(self, completion_llm, is_verbose=False):
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose

    def get_tools(self):
        wiki_search = HotpotExample(self.completion_llm, self.is_verbose)

        return [
          Tool(
              name="Search",
              func=wiki_search.run,
              description="useful to search for the truth"
          )
        ]
