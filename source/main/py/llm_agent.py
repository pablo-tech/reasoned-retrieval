from langchain.schema.messages import AIMessage
from langchain.prompts.base import StringPromptValue

from llm_memory import LlmMemory
# from llm_tool import ToolFactory
from llm_template import PromptFactory
# PipelinedAgentTemplateBank
from llm_executor import FinalAnswer
from react_parser import OptimisticParser

# from typing_extensions import ParamSpecKwargs


class PipelinedAgent():

    def __init__(self,
                 agent_llm,
                 agent_tools,
                 agent_prompt,
                 agent_parser,
                 memory_factory,
                 response_template=None,
                 is_verbose=True):

        self.agent_llm = agent_llm
        self.agent_tools = agent_tools
        self.incomplete_prompt = agent_prompt
        self.agent_parser = agent_parser
        self.memory_factory = memory_factory
        self.response_template = response_template
        self.is_verbose = is_verbose

    def invoke(self, executor_input):
        # print("\nAGENT_LLM=>"+str(self.get_llm()))
        # print("\nAGENT_TOOLS=>"+str(self.get_tools()))
        # print("\nEXECUTOR_INPUT=>"+str(executor_input.__str__()))
        prompt = self.incomplete_prompt
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

    def filled_prompt(self, incomplete_prompt, executor_input):
        return incomplete_prompt.invoke(executor_input.str_values())

    def set_stop(self, stop_txts=["\nObservation"]):
        self.agent_llm = self.agent_llm.bind(stop=stop_txts)

    def get_llm(self):
        return self.agent_llm

    def get_tools(self):
        return self.agent_tools

    def get_prompt(self):
        return self.incomplete_prompt

    def get_parser(self):
        return self.agent_parser

    def filled_str(self, prompt):
        if not isinstance(prompt, StringPromptValue):
            s = ""
            for m in prompt.messages:
              s += m.content
            return s
        return str(prompt.text)    


class AgentFactory():

    def __init__(self,
                 inference_agent_llm,
                 chat_agent_llm,
                 is_verbose=True):
        self.inference_agent_llm = inference_agent_llm
        self.chat_agent_llm = chat_agent_llm
        self.inference_prompt_factory = PromptFactory(self.inference_agent_llm)
        self.chat_prompt_factory = PromptFactory(self.chat_agent_llm)
        self.is_verbose = is_verbose

    def react_solve_agent(self,
                          tool_factory_func,
                          memory_factory=None,
                          agent_parser=OptimisticParser()):

        agent_tools = tool_factory_func(self.inference_agent_llm)
        incomplete_prompt = PromptFactory(self.inference_agent_llm).react_fewshot(tool_set=agent_tools)

        return PipelinedAgent(agent_llm=self.inference_agent_llm,
                              agent_tools=agent_tools,
                              agent_prompt=incomplete_prompt,
                              agent_parser=agent_parser,
                              memory_factory=memory_factory,
                              is_verbose=self.is_verbose)

    def react_converse_agent(self,
                             tool_factory_func,
                             memory_factory=LlmMemory.conversation_buffer,
                             agent_parser=OptimisticParser()):

        agent_tools = tool_factory_func(self.chat_agent_llm)
        incomplete_prompt = PromptFactory(self.chat_agent_llm).react_fewshot(tool_set=agent_tools)
        return PipelinedAgent(agent_llm=self.chat_agent_llm,
                              agent_tools=agent_tools,
                              agent_prompt=incomplete_prompt,
                              agent_parser=agent_parser,
                              memory_factory=memory_factory,
                              is_verbose=self.is_verbose)