from tool_hotpot import HotpotToolFactory
from model_bot import ChatBot

class ThoughtTracer():

    def __init__(self, completion_llm, is_verbose):
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose

    def thought_traces(self, tools, question):
        inferrence = ""
        try:
            bot = ChatBot(agent_llm=self.completion_llm,
                            agent_tools=tools,
                            is_verbose=self.is_verbose)
            inferrence = bot.invoke(question)
        except Exception as e:
            print("QUESTIONER_ERROR="+str(e)+"..."+str(question))
            print("\n")
            pass
        return inferrence  

    def hotpot_traces(self, data):
        tools = HotpotToolFactory(self.completion_llm).get_tools()
        return self.thought_traces(tools, data)

