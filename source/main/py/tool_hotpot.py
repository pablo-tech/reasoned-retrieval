import json

from langchain.agents import Tool

from llm_run import ToolRun

    

class HotpotDataset(ToolRun):
    # https://pypi.org/project/wikipedia/

    def __init__(self, completion_llm, is_verbose=False):
        super().__init__()
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose
        hotpot_train = '/content/drive/MyDrive/StanfordLLM/hotpot_qa/hotpot_train_v1.1.json'
        with open(hotpot_train) as json_file:
            self.data = json.load(json_file) 


class HotpotStore(HotpotDataset):

    def __init__(self, completion_llm, is_verbose=False):
        super().__init__(completion_llm, is_verbose)
        self.doc_store = {}
        for example in self.data:
            contexts = example['context']
            contexts = ["".join(context[1]) for context in contexts]
            self.doc_store[example['question']] = contexts        


class HotpotExample(HotpotStore):

    def __init__(self, completion_llm, is_verbose=False):
        super().__init__(completion_llm, is_verbose)

    def run(self, tool_input, user_query):
        return self.invoke(user_query, self.select)

    def select(self, query):
        return self.answer(self.summarize(self.subquery(query)))

    def answer(self, results):
        return [result for result in results]

    def summarize(self, results):
        return [result for result in results]

    def subquery(self, query):
        try:
          return self.doc_store[query]
        except Exception as e:
          # print("SEARCH_SUBQUERY_ERROR=" + str(e))
          return [str(e)]


class HotpotToolFactory():

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
