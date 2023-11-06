from llm_executor import ExecutorFactory
from llm_memory import LlmMemory


class ChatBot():

    def __init__(self, agent_llm, agent_tools, is_verbose):
        self.is_verbose = is_verbose
        self.executor_factory = ExecutorFactory(agent_llm=agent_llm,
                                                is_verbose=is_verbose)
        self.executor = self.executor_factory.react_executor(agent_tools=agent_tools,
                                                            agent_memory=LlmMemory())
        self.react_agent = self.executor.get_agent()

    def invoke(self, query):
        response = self.executor.invoke(user_query=query)
        return response

    def reduce(self):
        pass

