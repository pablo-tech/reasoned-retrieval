from tool_hotpot import HotpotToolFactory
from model_bot import ChatBot

import textwrap

from collections import defaultdict


class ThoughtTracer():

    def __init__(self, is_verbose):
        self.is_verbose = is_verbose

    def thought_traces(self, named_llms, tools, data, 
                       n, width=75):
        traces = defaultdict(dict)

        for i in range(n):
            example = data[i]
            question = example['question'].strip()
            correct_answer = example['answer'] 
            print("\n\n=========\n")
            print(textwrap.fill("--> " + str(question), width))
            print(textwrap.fill("CORRECT => " + correct_answer, width)) 
            for name, llm in named_llms.items():
                try:
                    name = name.upper()
                    inferred_response = None
                    bot = ChatBot(agent_llm=llm,
                                  agent_tools=tools,
                                  is_verbose=self.is_verbose)
                    inferred_response = bot.invoke(question)
                    traces[name][question] = inferred_response
                    if inferred_response is not None and inferred_response.get_answer() is not None:    
                        print(str(name) + " => " + str(inferred_response.get_answer()))
                    else:
                        print(str(name) + " => " + "None")

                except Exception as e:
                    # print(str(name) + " => " + str(inferred_response.get_answer()))
                    # pass 
                    print(str(name.upper()) + " => ERROR..." + str(e) + "\n... INFERRED=> " + str(inferred_response)) 
        return traces  

    def hotpot_traces(self, named_llms, data, n):
        tools = HotpotToolFactory(named_llms).get_tools()
        return self.thought_traces(named_llms, tools, data, n)
