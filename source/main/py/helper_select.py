from llm_run import ToolRun


class SelectHelper(ToolRun):

    def __init__(self, model_name, completion_llm, is_verbose):
        super().__init__(model_name)
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose

    def answer(self, results, query):
        return [result for result in results]

    def summarize(self, results, query):
        return [result for result in results]
