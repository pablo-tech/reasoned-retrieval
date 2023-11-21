from langchain.agents import Tool

from vector_db import PineconeDb

from helper_select import SelectHelper


class VectorRetriever(SelectHelper):
    # https://pypi.org/project/wikipedia/

    def __init__(self, completion_llm, is_verbose=False):
        super().__init__("PINECONE", completion_llm, is_verbose)
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose
        self.doc_store = PineconeDb(index_name="quickstart",
                                    is_create=True)
        print(self.doc_store.__str__())


class VectorSearchReader(VectorRetriever):

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
          results = self.doc_store.search(query, k)
        except Exception as e:
          # print("SEARCH_SUBQUERY_ERROR=" + str(e))
          return [str(e)]
        return results
        # snippets = []
        # for result in results:
        #   try:
        #     snippets.append(self.doc_store.summary(result,
        #                                            sentences=n))
        #   except Exception as e:
        #     # print("SEARCH_SUMMARIZE_ERROR=" + str(e))
        #     pass
        #   if len(snippets) >= k:
        #     return snippets
        # return snippets


class VectorToolFactory():

    def __init__(self, completion_llm, is_verbose=False):
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose

    def get_tools(self):
        search = VectorSearchReader(self.completion_llm, self.is_verbose)

        return [
          Tool(
              name="Search",
              func=search.run,
              description="useful to search for the truth"
          )
        ]
