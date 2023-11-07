import json

from langchain.agents import Tool

from llm_select import ToolSelect

    
class HotpotDataset(ToolSelect):
    # https://pypi.org/project/wikipedia/

    def __init__(self, completion_llm, is_verbose):
        super().__init__("HOTPOT")
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose
        hotpot_train = '/content/drive/MyDrive/StanfordLLM/hotpot_qa/hotpot_train_v1.1.json'
        with open(hotpot_train) as json_file:
            self.data = json.load(json_file) 


class HotpotRetriever(HotpotDataset):

    def __init__(self, completion_llm, is_verbose):
        super().__init__(completion_llm, is_verbose)
        self.doc_store = {}
        for example in self.data:
            contexts = example['context']
            contexts = ["".join(context[1]) for context in contexts]
            self.doc_store[example['question'].strip()] = contexts        

    def subquery(self, query):
        try:
          return self.doc_store[query]
        except Exception as e:
          error = "HOTPOT_SUBQUERY_ERROR="+str(e)+"...WITH_QUERY="+str(query)
          print(error)
          return [error]


class HotpotReader(HotpotRetriever):

    def __init__(self, completion_llm, is_verbose):
        super().__init__(completion_llm, is_verbose)

    def run(self, tool_input, user_query):
        return self.invoke(user_query, self.select)

    def select(self, query):
        results = self.subquery(query)
        return self.answer(self.summarize(results, query), query)


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
