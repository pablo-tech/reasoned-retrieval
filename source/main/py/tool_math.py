from langchain.chains import LLMMathChain
from langchain.agents import Tool

from pydantic import BaseModel, Field


class CalculatorInput(BaseModel):
    question: str = Field()


class MathAnswer():

    def __init__(self, completion_llm):
        self.math_engine = LLMMathChain(llm=completion_llm, 
                                        verbose=True)
        self.math_tool = Tool.from_function(
                func=self.math_engine.run,
                name="Calculator",
                description="useful for when you need to answer questions about math",
                args_schema=CalculatorInput
                # coroutine= ... <- you can specify an async method if desired as well
        )

    def run(self, query):
        result = self.math_tool.run(query)
        try:
            return eval(result.replace('Answer: ', ''))
        except:
            return result
        

class PythonMathFactory():

    def math_tools(completion_llm):
        math_api = MathAnswer(completion_llm) 
        return [
            Tool(
              name="Calculate",
              func=math_api.run,
              description="useful to answer math questions"
        )]

            