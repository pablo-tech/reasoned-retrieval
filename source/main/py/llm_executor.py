from langchain.schema.messages import AIMessage
from langchain.prompts.base import StringPromptValue
from langchain.schema import AgentAction, AgentFinish

from llm_template import TemplateBank
from llm_tool import ToolFactory


# https://python.langchain.com/docs/modules/agents/
# https://python.langchain.com/docs/modules/agents/
# https://python.langchain.com/docs/integrations/toolkits/
# https://github.com/langchain-ai/langchain/tree/master/cookbook
class ExecutorInput():

    def __init__(self):
        self.template_vars = {}
        self.agent_scratchpad = []
        self.chat_history = []

    def template_values(self, template_vars):
        for key, value in template_vars.items():
          self.template_vars[key] = value

    def template_value(self, key, value):
        self.template_vars[key] = value

    def add_step(self, agent_action, step_observation):
        if isinstance(step_observation, str):
            step_observation = step_observation.strip()
        step = (agent_action, step_observation)
        self.agent_scratchpad.append(step)

    def get_steps(self):
        return self.agent_scratchpad

    def str_values(self):
        template_settings = self.template_vars.copy()
        template_settings["chat_history"] = self.chat_history
        template_settings["agent_scratchpad"] = self.format_log_to_str()
        return template_settings

    def format_log_to_str(self,
                          observation_prefix="Observation: "):
        thoughts = ""
        for thought_action, observation in self.agent_scratchpad:
            thought_action = thought_action.log.strip()
            thoughts += f"{thought_action}" + "\n"
            thoughts += f"{observation_prefix}" + str(observation) + "\n"
        return thoughts

    def __str__(self):
        s = ""
        for k, v in self.str_values().items():
            s += "- " + str(k.upper()) + ": " + "\n" + str(v) + "\n"
        return s
    

class PipelinedAgent():

    def __init__(self,
                 agent_llm,
                 agent_tools,
                 agent_prompt,
                 agent_parser,
                 memory_factory,
                 response_template=None,
                 is_verbose=False):

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
    

class FinalAnswer():

    def __init__(self, answer, steps, exception):
        self.answer = answer
        self.steps = steps
        self.exception = exception
        self.is_success = True
        if isinstance(answer, AgentAction):
            self.answer = answer.log
            self.is_success = False
        if isinstance(answer, AgentFinish):
            self.answer = answer.return_values['output']
        if answer is None:
            self.is_success = False

    def __str__(self):
        s = "FINAL_ANSWER=>" + "\n"
        s += " - success: " + str(self.is_success) + "\n"
        s += " - ANSWER: " + "\n" + str(self.answer) + "\n"
        s += " - steps: " + "\n"
        for step in self.steps:
          s += "\t" + "parsed: " + str(step[0]) + "\n"
          s += "\t" + "observation: " + str(step[1]) + "\n"
        s += " - exception=> " + "\n"
        for entry in self.exception:
          s += "\t" + "input: " + str(entry[0]) + "\n"
          s += "\t" + "exception: " + str(entry[1]) + "\n"
        return s    
    

class PipelinedExecutor():
# https://api.python.langchain.com/en/latest/_modules/langchain/agents/agent.html#AgentExecutor

    def __init__(self,
                 llm_agent,
                 max_iterations,
                 max_execution_time,
                 agent_stop=["Observation"],
                 is_verbose=False):
        # save
        self.llm_agent = llm_agent
        self.llm_agent.set_stop(agent_stop)
        self.agent_tools = self.llm_agent.get_tools()
        self.max_iterations = max_iterations
        self.max_execution_time = max_execution_time
        self.is_verbose = is_verbose
        # input
        self.executor_input = ExecutorInput()
        self.executor_input.template_value("fewshot_examples", TemplateBank.REACT_DOC_STORE_JOINT_ACTION)
        # error
        self.error_log = []

    def invoke(self, user_query):
        self.executor_input.template_value("input_question", user_query)
        remain_iterations = self.max_iterations

        while remain_iterations > 0:
            try:
              parsed = self.llm_agent.invoke(self.executor_input)

              if isinstance(parsed, AgentAction):
                # try:
                tool_name = parsed.tool
                tool_input = parsed.tool_input
                if tool_name not in ToolFactory().tool_names(self.agent_tools):
                    observation = tool_name + " is not a valid action to take."
                else:
                    tool = [t for t in self.agent_tools if t.name==tool_name][0]
                    observation = tool.func(tool_input)
                self.executor_input.add_step(parsed, observation)
                if self.is_verbose:
                    print(self.tool_observation(tool_name, tool_input, observation))

              if isinstance(parsed, AgentFinish):
                    self.executor_input.add_step(parsed, "Finish Action")              
                    return FinalAnswer(parsed, self.executor_input.get_steps(), self.error_log)

            except Exception as e:
                self.error_log.append((self.executor_input.str_values(), str(e)))

            remain_iterations-=1
            if remain_iterations == 0:
                if self.is_verbose:
                    print("TIMEOUT...")
                return FinalAnswer(None, self.executor_input.get_steps(), self.error_log)

    def tool_observation(self, tool, input, observation):
        s = "\n\nTOOL_INVOCATION=>" + "\n"
        s += "- tool: " + str(tool) + "\n"
        s += "- input: " + str(input) + "\n"
        s += "- observation: " + str(observation) + "\n"
        return s