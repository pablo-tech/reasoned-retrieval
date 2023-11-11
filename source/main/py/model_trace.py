from tool_hotpot import HotpotToolFactory
from model_bot import ChatBot

import textwrap

from collections import defaultdict


class ThoughtTracer():

    def __init__(self, named_llms, is_verbose):
        self.named_llms = named_llms
        self.is_verbose = is_verbose

    def thought_traces(self, name, llm, tools, data, n):
        question_traces = {}

        for i in range(n):
            example = data[i]
            question = example['question'].strip()
            correct_answer = example['answer'] 
            try:
                bot = ChatBot(agent_llm=llm,
                                agent_tools=tools,
                                is_verbose=self.is_verbose)
                inferred_response = bot.invoke(question)
                question_traces[question] = inferred_response
                width=75  
                print(textwrap.fill(str(question), width))
                print(textwrap.fill("CORRECT=" + correct_answer, width)) 
                print(textwrap.fill(name + " " + "INFERRED=" + inferred_response.get_answer(), width))

            except Exception as e:
                print("QUESTIONER_ERROR="+str(e)+"..."+str(question))
                print("\n")
                pass
        return question_traces  

    def hotpot_traces(self, named_llms, data, n):
        model_traces = defaultdict(list)
        for name, llm in named_llms.items():
            tools = HotpotToolFactory(self.completion_llm).get_tools()
            question_traces = self.thought_traces(name, llm, tools, data, n)
            model_traces[name].add(question_traces)
        return model_traces