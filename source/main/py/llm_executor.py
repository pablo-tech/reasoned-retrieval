from langchain.schema import AgentAction, AgentFinish

from llm_template import TemplateBank
from llm_tool import ToolFactory
from llm_template import ReactDescribe
from llm_memory import LlmMemory
from llm_agent import AgentFactory

# https://python.langchain.com/docs/modules/agents/
# https://python.langchain.com/docs/modules/agents/
# https://python.langchain.com/docs/integrations/toolkits/
# https://github.com/langchain-ai/langchain/tree/master/cookbook


class FinalAnswer():

    def __init__(self, agent_step, executor_steps, execution_error):
        self.agent_answer = None
        self.executor_steps = executor_steps
        self.execution_error = execution_error
        self.is_finish = False
        self.log = ''
        if isinstance(agent_step, AgentAction):
            self.agent_answer = agent_step.log
        if isinstance(agent_step, AgentFinish):
            self.agent_answer = agent_step.return_values['output']
            self.log = agent_step.log
            self.is_finish = True

    def get_answer(self):
        return self.agent_answer
    
    def get_steps(self):
        return self.executor_steps
    
    def get_finish(self):
        return self.is_finish
    
    def get_thought_action(self):
        return self.log

    def __str__(self):
        s = "FINAL_ANSWER=>" + "\n"
        s += " - NORMAL_FINISH: " + str(self.get_finish()) + "\n"
        s += " - FULL_RESPONSE: " + "\n" 
        s += "\t" + "Answer... " + str(self.get_answer()) + "\n"
        s += "\t" + "Thought-Action..." + str(self.get_thought_action().replace("\n", " ")) + "\n"
        s += " - EXECUTOR_STEPS: " + "\n"
        # for step in self.executor_steps:
        #   s += "\t" + "parsed: " + str(step[0]) + "\n"
        #   s += "\t" + "observation: " + str(step[1]) + "\n"
        s += " - EXCECUTION_EXCEPTION => " + "\n"
        for error, input in self.execution_error.get_error_input():
          s += "\t" + "context_values: " + str(input) + "\n"
          s += "\t" + "exception: " + str(error) + "\n"
        return s
    

class ContextValues():

    def __init__(self):
        self.template_vars = {}
        self.set_scratchpad("")
        self.set_history("")

    def template_values(self, key_values):
        for key, value in key_values.items():
            self.template_vars[key] = value

    def template_value(self, key, value):
        self.template_vars[key] = value

    def set_scratchpad(self, execution_journey):
        self.template_vars["agent_scratchpad"] = execution_journey.__str__()

    def get_scratchpad(self):
        return self.template_vars["agent_scratchpad"]
    
    def set_history(self, chat_history):
        self.template_vars["chat_history"] = chat_history.__str__()

    def get_history(self):
        return self.template_vars["chat_history"]

    def get_values(self):
        return self.template_vars
    
    # def __str__(self):
    #     s = ""
    #     for k, v in self.str_values().items():
    #         s += "- " + str(k.upper()) + ": " + "\n" + str(v) + "\n"
    #     return s
        

class ExecutionJourney():

    def __init__(self):
        self.agent_scratchpad = []

    def add_step(self, agent_action, step_observation):
        if isinstance(step_observation, str):
            step_observation = step_observation.strip()
        step = (agent_action, step_observation)
        self.agent_scratchpad.append(step)

    def __str__(self, observation_prefix="Observation: "):
        thoughts = ""
        for thought_action, observation in self.agent_scratchpad:
            thought_action = thought_action.log.strip()
            thoughts += f"{thought_action}" + "\n"
            thoughts += f"{observation_prefix}" + str(observation) + "\n"
        return thoughts
    

class ExecutionError():

    def __init__(self):
        self.error_log = []

    def error_input(self, error, input):
        self.error_log.append((error, input))

    def get_error_input(self):
        return self.error_log
    


class PipelinedExecutor():
# https://api.python.langchain.com/en/latest/_modules/langchain/agents/agent.html#AgentExecutor

    def __init__(self,
                 llm_agent,
                 max_iterations,
                 max_execution_time,
                 agent_stop=["Observation"],
                 is_verbose=True):
        # save
        self.llm_agent = llm_agent
        self.llm_agent.set_stop(agent_stop)
        self.agent_tools = self.llm_agent.get_tools()
        self.max_iterations = max_iterations
        self.max_execution_time = max_execution_time
        self.is_verbose = is_verbose
        # input
        self.context_values = ContextValues()
        self.context_values.template_value("fewshot_examples", TemplateBank.REACT_DOC_STORE_JOINT_ACTION)
        # journey
        self.execution_journey = ExecutionJourney()
        self.execution_error = ExecutionError()

    def invoke(self, user_query):
        self.context_values.template_value("input_question", user_query)
        remain_iterations = self.max_iterations

        while remain_iterations > 0:
            try:
                agent_step, observation = None, None
                self.context_values.set_history(self.llm_agent.get_memory().__str__())
                self.context_values.set_scratchpad(self.execution_journey)
                agent_step = self.llm_agent.invoke(self.context_values)

                if isinstance(agent_step, AgentAction):
                    tool_name, tool_input = agent_step.tool, agent_step.tool_input
                    if tool_name in ToolFactory().tool_names(self.agent_tools):
                        tool = [t for t in self.agent_tools if t.name==tool_name][0]
                        observation = tool.func(tool_input)
                        if self.is_verbose:
                            print(self.tool_observation(tool_name, tool_input, observation))
                    elif tool_name == "Describe" and tool_input == 'format':
                        observation = ReactDescribe().react_format() 
                        observation += ReactDescribe().name_template(self.llm_agent.get_tool_names())
                    elif tool_name == "List" and tool_input == 'tools':
                        observation = ReactDescribe().name_template(self.llm_agent.get_tool_names())
                    elif tool_name == "Describe" and tool_input == 'tools':
                        observation = ReactDescribe().summary_template(self.llm_agent.get_tool_summaries())
                    elif tool_name not in ToolFactory().tool_names(self.agent_tools):
                        observation = tool_name + " is not a valid action available to the agent. "
                        observation += "Try: 'Thought: I need to describe the tools available to the agent\nAction: Describe[tools]'."

                if isinstance(agent_step, AgentFinish):
                        self.execution_journey.add_step(agent_step, "EXECUTION_DONE") 
                        final = FinalAnswer(agent_step, self.context_values.get_scratchpad(), self.execution_error)
                        self.llm_agent.get_memory().message_exchange(user_query, final.get_answer())             
                        return final

                self.execution_journey.add_step(agent_step, observation)                

            except Exception as e:
                self.execution_error.error_input(str(e), input)

            remain_iterations-=1
            if remain_iterations == 0:
                if self.is_verbose:
                    print("TIMEOUT...")
                return FinalAnswer(None, self.context_values.get_scratchpad(), self.execution_error)

    def tool_observation(self, tool, input, observation):
        s = "\n\nTOOL_INVOCATION=>" + "\n"
        s += "- tool: " + str(tool) + "\n"
        s += "- input: " + str(input) + "\n"
        s += "- observation: " + str(observation) + "\n"
        return s
    
    def get_agent(self):
        return self.llm_agent


class ExecutorFactory():

    def __init__(self,
                 agent_llm,
                 is_verbose=True):
        self.is_verbose = is_verbose
        self.agent_llm = agent_llm
        self.agent_factory = AgentFactory(self.agent_llm,
                                          is_verbose=is_verbose)

    def llm_executor(self):
        ''' Direct Inference '''
        return self.agent_llm

    def cot_executor(self):
        ''' Chain of Thought '''
        return self.agent_llm

    def react_executor(self,
                       tool_factory_func,
                       agent_memory=LlmMemory(),
                       max_iterations=10,
                       max_execution_time=None):
        ''' ReAct Inference Solve '''
        react_agent = self.agent_factory.react_agent(tool_factory_func=tool_factory_func,
                                                     agent_memory=agent_memory)
        return PipelinedExecutor(llm_agent=react_agent,
                                 max_iterations=max_iterations,
                                 max_execution_time=max_execution_time,
                                 is_verbose=self.is_verbose)