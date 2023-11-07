import time

from langchain.chains import LLMMathChain
from langchain.agents import Tool

from pydantic import BaseModel, Field

from llm_select import ToolSelect


class CalculatorInput(BaseModel):
    question: str = Field()


class MathAnswer(ToolSelect):

    def __init__(self, completion_llm, is_verbose):
        super().__init__(completion_llm, is_verbose)
        self.math_engine = LLMMathChain(llm=completion_llm, 
                                        verbose=is_verbose)
        self.math_tool = Tool.from_function(
                func=self.math_engine.run,
                name="Calculator",
                description="useful for when you need to answer questions about math",
                args_schema=CalculatorInput
                # coroutine= ... <- you can specify an async method if desired as well
        )

    def run(self, tool_input, user_query=""):
        return self.invoke(tool_input, self.select)
    
    def select(self, query):
        results = self.subquery(query)
        return self.answer(self.summarize(results, query), query)

    # def answer(self, results):
    #     return [result for result in results]
    
    # def summarize(self, results):
    #     try:
    #         return [eval(result.replace('Answer: ', '')) for result in results]
    #     except:
    #         pass
    #     return []

    def subquery(self, query):
        results = [self.math_tool.run(query)]
        try:
            return [eval(result.replace('Answer: ', '')) for result in results]
        except:
            pass
        return results        

        
class MathToolFactory():

    def __init__(self, completion_llm, is_verbose=False):
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose

    def get_tools(self):
        api = MathAnswer(self.completion_llm, self.is_verbose) 
        return [
            Tool(
              name="Calculate",
              func=api.run,
              description="useful to answer math questions"
        )]

            