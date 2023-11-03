import time

from langchain.chains import LLMMathChain
from langchain.agents import Tool

from pydantic import BaseModel, Field

from llm_run import ModelRun
from llm_run import ModelRun, RunAnswer
from llm_step import FinishStep


class CalculatorInput(BaseModel):
    question: str = Field()


class MathAnswer(ModelRun):

    def __init__(self, completion_llm, is_verbose):
        super().__init__()
        self.math_engine = LLMMathChain(llm=completion_llm, 
                                        verbose=is_verbose)
        self.math_tool = Tool.from_function(
                func=self.math_engine.run,
                name="Calculator",
                description="useful for when you need to answer questions about math",
                args_schema=CalculatorInput
                # coroutine= ... <- you can specify an async method if desired as well
        )

    def run(self, query):
        return self.invoke(query, self.calculate)

    def calculate(self, query):
        result = self.math_tool.run(query)
        try:
            result = eval(result.replace('Answer: ', ''))
        except:
            pass
        return result

    # def run(self, query):
    #     result = self.math_tool.run(query)
    #     try:
    #         result = eval(result.replace('Answer: ', ''))
    #     except:
    #         pass
    #     model_step = FinishStep(result, action_log="")
    #     self.run_journey.add_run(model_step, "EXECUTION_DONE") 
    #     return RunAnswer(model_step, self.run_journey, 
    #                      self.run_error, self.run_measure)
        # return result
        

class MathToolFactory():

    def __init__(self, completion_llm, is_verbose=False):
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose

    def math_tools(self):
        math_api = MathAnswer(self.completion_llm, self.is_verbose) 
        return [
            Tool(
              name="Calculate",
              func=math_api.run,
              description="useful to answer math questions"
        )]

            