from langchain.agents import Tool
from langchain import Wikipedia
from langchain.agents.react.base import DocstoreExplorer

from llm_run import ModelRun
from llm_run import ModelRun, RunAnswer
from llm_step import FinishStep


class WikipediaSearch(ModelRun):

    def __init__(self):
        super().__init__()
        self.doc_store = DocstoreExplorer(Wikipedia())

    def run(self, query):
        model_step = FinishStep(self.doc_store.search(query), log="")
        self.run_journey.add_step(model_step, "EXECUTION_DONE") 
        return RunAnswer(model_step, self.run_journey, 
                         self.run_error, self.run_measure)
        # return self.doc_store.search(query)

class WikipediaLookup(ModelRun):

    def __init__(self):
        super().__init__()
        self.doc_store = DocstoreExplorer(Wikipedia())

    def run(self, query):
        model_step = FinishStep(self.doc_store.lookup(query), log="")
        self.run_journey.add_step(model_step, "EXECUTION_DONE") 
        return RunAnswer(model_step, self.run_journey, 
                         self.run_error, self.run_measure)
        # return self.doc_store.lookup(query)


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
