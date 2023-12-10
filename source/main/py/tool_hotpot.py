import json

from langchain.agents import Tool

from helper_select import SelectHelper
from domain_evaluation import HotpotDataset
    

class HotpotRetriever(SelectHelper):

    def __init__(self, completion_llm, is_verbose):
        super().__init__("HOTPOT", completion_llm, is_verbose)
        self.hotpot_data = HotpotDataset(completion_llm, is_verbose)
        self.doc_store = {}
        for example in self.hotpot_data.get_corpus():
            contexts = example['context']
            contexts = ["".join(context[1]) for context in contexts]
            self.doc_store[example['question'].strip()] = contexts        

    def subquery(self, query_txt, query_filter):
        try:
          return self.doc_store[query_txt]
        except Exception as e:
          error = "HOTPOT_SUBQUERY_ERROR="+str(e)+"...WITH_QUERY="+str(query_txt)
          print(error)
          return [error]


class HotpotReader(HotpotRetriever):

    def __init__(self, completion_llm, is_verbose):
        super().__init__(completion_llm, is_verbose)

    def run(self, tool_input="", user_query="", query_filter={}):
        return self.invoke(user_query, query_filter, self.select)

    def select(self, query_txt, query_filter):
        results = self.subquery(query_txt, query_filter)
        return self.answer(self.summarize(results, query_txt), query_txt)


class HotpotToolFactory():

    def __init__(self, completion_llm, is_verbose=False):
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose

    def get_tools(self):
        api = HotpotReader(self.completion_llm, self.is_verbose)
        return [
          Tool(
              name="Search",
              func=api.run,
              description="useful to search for the truth"
          )
        ]
