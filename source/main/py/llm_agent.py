from langchain.schema.messages import AIMessage
from langchain.prompts.base import StringPromptValue

from llm_memory import LlmMemory
from react_template import PromptFactory
from react_parser import OptimisticParser
from tool_factory import ToolFactory


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
        self.agent_parser = agent_parser
        self.agent_memory = agent_memory
        self.response_template = response_template
        self.is_verbose = is_verbose
        self.prompt_factory = prompt_factory

    def invoke(self, executor_input):
        # print("\nAGENT_LLM=>"+str(self.get_llm()))
        # if self.is_verbose:
        #     print("\nAGENT_TOOLS=>"+str(self.get_tool_names()))
        # print("\nEXECUTOR_INPUT=>"+str(executor_input.__str__()))
        prompt = self.prompt_factory.react_fewshot()
        # print("\nINCOMPLETE_PROMPT=>"+str(prompt))
        prompt = self.filled_prompt(prompt, executor_input)
        input_len = len(prompt.to_string())
        # print("\n\nFILLED_PROMPT=>"+self.filled_str(prompt) + "\n\n")
        inferred = self.agent_llm.invoke(prompt)
        if isinstance(inferred, AIMessage):
            try:
                inferred = inferred.content
            except:
                inferred = ''
        output_len = len(inferred)
        # if self.is_verbose:
        # print("\nINFERRED=>"+"\n"+str(inferred))
        agent_step = self.agent_parser.parse(inferred)
        # if self.is_verbose:
        #     print("\nPARSED=>"+str(agent_step)+"\n\n")
        return agent_step, prompt.to_string(), input_len, output_len

    def filled_prompt(self, incomplete_prompt, context_values):
        return incomplete_prompt.invoke(context_values.get_values())

    def set_stop(self, stop_txts=["\nObservation"]):
        self.agent_llm = self.agent_llm.bind(stop=stop_txts)

    def get_llm(self):
        return self.agent_llm

    def get_tools(self):
        return self.agent_tools
    
    def get_tool_names(self):
        return ToolFactory.tool_names(self.get_tools())

    def get_tool_summaries(self):
        return ToolFactory.tool_summaries(self.get_tools())

    def get_prompt(self):
        return self.incomplete_prompt

    def get_parser(self):
        return self.agent_parser
    
    def get_memory(self):
        return self.agent_memory

    # def prompt_str(self, prompt):
    #     if not isinstance(prompt, StringPromptValue):
    #         s = ""
    #         for m in prompt.messages:
    #           s += m.content
    #         return s
    #     return str(prompt.text)    


class AgentFactory():

    def __init__(self,
                 agent_llm,
                 is_verbose=True):
        self.agent_llm = agent_llm
        self.prompt_factory = PromptFactory(self.agent_llm)
        self.is_verbose = is_verbose

    def react_agent(self,
                    agent_tools,
                    agent_memory=LlmMemory(),
                    agent_parser=OptimisticParser()):

        return PipelinedAgent(agent_llm=self.agent_llm,
                              agent_tools=agent_tools,
                              prompt_factory=self.prompt_factory,
                              agent_parser=agent_parser,
                              agent_memory=agent_memory,
                              is_verbose=self.is_verbose)
    