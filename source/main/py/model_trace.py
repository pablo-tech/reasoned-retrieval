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
            print(textwrap.fill("\n\n--> " + str(question), width))
            print(textwrap.fill("CORRECT => " + correct_answer, width)) 
            try:
                for name, llm in named_llms.items():
                    bot = ChatBot(agent_llm=llm,
                                  agent_tools=tools,
                                  is_verbose=self.is_verbose)
                    inferred_response = bot.invoke(question)
                    traces[name][question] = inferred_response
                    print(textwrap.fill(str(name.upper()) + " => " + inferred_response.get_answer(), width))

            except Exception as e:
                print(str(name.upper()) + " => " + str(e)) 
        return traces  

    def hotpot_traces(self, named_llms, data, n):
        tools = HotpotToolFactory(named_llms).get_tools()
        return self.thought_traces(named_llms, tools, data, n)
