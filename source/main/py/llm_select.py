from llm_run import ToolRun


class ToolSelect(ToolRun):

    def __init__(self, completion_llm, is_verbose):
        super().__init__()
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose

    def answer(self, results, query):
        return [result for result in results]

    def summarize(self, results, query):
        return [result for result in results]
