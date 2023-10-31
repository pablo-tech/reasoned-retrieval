from langchain.schema.messages import AIMessage
from langchain.prompts.base import StringPromptValue

from llm_memory import LlmMemory
from llm_template import PromptFactory
from react_parser import OptimisticParser
from llm_tool import ToolFactory


class PipelinedAgent():

    def __init__(self,
                 agent_llm,
                 agent_tools,
                 agent_parser,
                 agent_memory,
                 prompt_factory,
                 response_template=None,
                 is_verbose=True):

        self.agent_llm = agent_llm
        self.agent_tools = agent_tools
        # self.incomplete_prompt = agent_prompt
        self.agent_parser = agent_parser
        self.agent_memory = agent_memory
        self.response_template = response_template
        self.is_verbose = is_verbose
        self.prompt_factory = prompt_factory
        # self.incomplete_prompt =  self.prompt_factory.react_fewshot(tool_set=agent_tools)

    def invoke(self, executor_input):
        # print("\nAGENT_LLM=>"+str(self.get_llm()))
        # if self.is_verbose:
        #     print("\nAGENT_TOOLS=>"+str(self.get_tool_names()))
        # print("\nEXECUTOR_INPUT=>"+str(executor_input.__str__()))
        prompt = self.prompt_factory.react_fewshot()
        # print("\nINCOMPLETE_PROMPT=>"+str(prompt))
        prompt = self.filled_prompt(prompt, executor_input)
        if self.is_verbose:
            print("\nFILLED_PROMPT=>"+self.filled_str(prompt))
        inferred = self.agent_llm.invoke(prompt)
        if isinstance(inferred, AIMessage):
            inferred = inferred.content
        if self.is_verbose:
            print("\nINFERRED=>"+"\n"+str(inferred))
        parsed = self.agent_parser.parse(inferred)
        if self.is_verbose:
            print("\nPARSED=>"+str(parsed)+"\n\n")
        return parsed

    def filled_prompt(self, incomplete_prompt, context_values):
        return incomplete_prompt.invoke(context_values.get_values())

    def set_stop(self, stop_txts=["\nObservation"]):
        self.agent_llm = self.agent_llm.bind(stop=stop_txts)

    def get_llm(self):
        return self.agent_llm

    def get_tools(self):
        return self.agent_tools
    
    def get_tool_names(self):
        return ToolFactory().tool_names(self.get_tools())

    def get_tool_summaries(self):
        return ToolFactory().tool_summaries(self.get_tools())

    def get_prompt(self):
        return self.incomplete_prompt

    def get_parser(self):
        return self.agent_parser
    
    def get_memory(self):
        return self.agent_memory

    def filled_str(self, prompt):
        if not isinstance(prompt, StringPromptValue):
            s = ""
            for m in prompt.messages:
              s += m.content
            return s
        return str(prompt.text)    


class AgentFactory():

    def __init__(self,
                 agent_llm,
                 is_verbose=True):
        self.agent_llm = agent_llm
        self.prompt_factory = PromptFactory(self.agent_llm)
        self.is_verbose = is_verbose

    def react_agent(self,
                    tool_factory_func,
                    agent_memory=LlmMemory(),
                    agent_parser=OptimisticParser()):

        agent_tools = tool_factory_func(self.agent_llm)
        return PipelinedAgent(agent_llm=self.agent_llm,
                              agent_tools=agent_tools,
                              prompt_factory=self.prompt_factory,
                              agent_parser=agent_parser,
                              agent_memory=agent_memory,
                              is_verbose=self.is_verbose)
    