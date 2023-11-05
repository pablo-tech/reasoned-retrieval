from tool_hotpot import HotpotToolFactory
from model_bot import ChatBot

import textwrap


class ThoughtTrace():

    def __init__(self, completion_llm, is_verbose):
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose

    def hotpot_trace(self, data, n):
        trace = {}

        for i in range(n):
            example = data[i]
            question = example['question'].strip()
            about = example['context'][0][0]
            correct_answer = example['answer'] 
            try:
                tools = HotpotToolFactory(self.completion_llm).get_tools()
                bot = ChatBot(agent_llm=self.completion_llm,
                            agent_tools=tools,
                            is_verbose=True)
                inferred_response = bot.invoke(question)
                trace[question] = inferred_response
                width=75  
                print(textwrap.fill(str(question), width))
                print(textwrap.fill("CORRECT=" + correct_answer, width)) 
                print(textwrap.fill("INFERRED=" + inferred_response.get_answer(), width))

            except Exception as e:
                print("QUESTIONER_ERROR="+str(e)+"..."+str(question))
                print("\n")
        return trace        