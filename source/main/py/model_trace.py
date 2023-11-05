from tool_hotpot import HotpotToolFactory
from model_bot import ChatBot

import textwrap


class ThoughtTracer():

    def __init__(self, completion_llm, is_verbose):
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose

    def thought_traces(self, tools, data, n):
        traces = {}

        for i in range(n):
            example = data[i]
            question = example['question'].strip()
            about = example['context'][0][0]
            correct_answer = example['answer'] 
            try:
                bot = ChatBot(agent_llm=self.completion_llm,
                              agent_tools=tools,
                              is_verbose=self.is_verbose)
                inferred_response = bot.invoke(question)
                traces[question] = inferred_response
                width=75  
                print(textwrap.fill(str(question), width))
                print(textwrap.fill("CORRECT=" + correct_answer, width)) 
                print(textwrap.fill("INFERRED=" + inferred_response.get_answer(), width))

            except Exception as e:
                print("QUESTIONER_ERROR="+str(e)+"..."+str(question))
                print("\n")
                pass
        return traces  

    def hotpot_traces(self, data, n):
        tools = HotpotToolFactory(self.completion_llm).get_tools()
        return self.thought_traces(tools, data, n)