import time

from langchain.agents import Tool
from langchain import Wikipedia
from langchain.agents.react.base import DocstoreExplorer

from llm_run import ModelRun
from llm_run import ModelRun, RunAnswer
from llm_step import FinishStep


class WikipediaExplorer(ModelRun):

    def __init__(self, completion_llm, is_verbose=False):
        super().__init__()
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose
        self.doc_store = DocstoreExplorer(Wikipedia())


class WikipediaSearch(WikipediaExplorer):

    def __init__(self, completion_llm, is_verbose=False):
        super().__init__(completion_llm, is_verbose)

    def run(self, query):
        model_step = FinishStep(self.doc_store.search(query), action_log="")
        self.run_journey.add_run(model_step, "EXECUTION_DONE") 
        return RunAnswer(model_step, self.run_journey, 
                         self.run_error, self.run_measure)

class WikipediaLookup(WikipediaExplorer):

    def __init__(self, completion_llm, is_verbose=False):
        super().__init__(completion_llm, is_verbose)

    def run(self, query):
        model_step = FinishStep(self.doc_store.lookup(query), action_log="")
        self.run_journey.add_run(model_step, "EXECUTION_DONE") 
        return RunAnswer(model_step, self.run_journey, 
                         self.run_error, self.run_measure)


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
