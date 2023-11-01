import time

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


class ContextValues():

    def __init__(self):
        self.template_vars = {}
        self.set_question("")
        self.set_examples("")
        self.set_scratchpad("")
        self.set_history("")

    def template_values(self, key_values):
        for key, value in key_values.items():
            self.template_vars[key] = value

    def template_value(self, key, value):
        self.template_vars[key] = value

    def set_question(self, question):
        self.template_value("input_question", question)

    def get_question(self):
        return self.template_vars["input_question"]
                       
    def set_examples(self, examples):
        self.template_value("fewshot_examples", examples)  

    def get_examples(self):
        return self.template_vars["fewshot_examples"]      

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
        return thoughts.strip()
    

class ExecutionError():

    def __init__(self):
        self.error_log = []

    def error_input(self, error, input):
        self.error_log.append((error, input))

    def get_error_input(self):
        return self.error_log
    
    def __str__(self):
        s = ""
        for error, input in self.error_log:
          s += "\t context_values: " + str(input) + "\n"
          s += "\t exception: " + str(error)
        return s.strip()
    

class ExecutionMeasure():

    def __init__(self):
        self.iteration_count = 0
        self.hallucination_count = 0
        self.input_len = []
        self.output_len = []
        self.agent_time = []
        self.tool_time = []

    def add_iteration(self, is_hallucination, 
                      input_len, output_len,
                      agent_time, tool_time):
        self.iteration_count += 1
        if is_hallucination:
            self.hallucination_count += 1
        self.input_len.append(input_len)
        self.output_len.append(output_len)
        self.agent_time.append(agent_time)
        self.tool_time.append(tool_time)        

    def get_hallucination_count(self):
        return self.hallucination_count
    
    def get_max_input_len(self):
        try:
            return max(self.input_len)
        except:
            return 0

    def get_total_input_len(self):
        try:
            return sum(self.input_len)
        except:
            return 0

    def get_max_output_len(self):
        try:
            return max(self.output_len)
        except:
            return 0

    def get_total_output_len(self):
        try:
            return sum(self.output_len)
        except:
            return 0
        
    def get_max_agent_time(self):
        try:
            return max(self.agent_time)
        except:
            return 0

    def get_total_agent_time(self):
        try:
            return sum(self.agent_time)
        except:
            return 0 

    def get_max_tool_time(self):
        try:
            return max(self.tool_time)
        except:
            return 0

    def get_total_tool_time(self):
        try:
            return sum(self.tool_time)
        except:
            return 0 

    def __str__(self):
        s = ""
        s += "\t hallucination_count: " + str(self.get_hallucination_count()) + "\n"
        s += "\t max_input_len: " + str(self.get_max_input_len()) + "\n"
        s += "\t total_input_len: " + str(self.get_total_input_len()) + "\n"
        s += "\t max_output_len: " + str(self.get_max_output_len()) + "\n"
        s += "\t total_output_len: " + str(self.get_total_output_len()) + "\n"
        s += "\t max_agent_time: " + "{:.3f}".format(self.get_max_agent_time()) + "\n"
        s += "\t total_agent_time: " + "{:.3f}".format(self.get_total_agent_time()) + "\n"
        s += "\t max_tool_time: " + "{:.3f}".format(self.get_max_tool_time()) + "\n"
        s += "\t total_tool_time: " + "{:.3f}".format(self.get_total_tool_time())        
        return s
    

class FinalAnswer():

    def __init__(self, 
                 agent_step, execution_journey, 
                 execution_error, execution_measure):
        ### save
        self.agent_answer = None
        self.execution_journey = execution_journey
        self.execution_error = execution_error
        self.execution_measure = execution_measure
        ### summarize
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
        
    def get_finish(self):
        return self.is_finish
    
    def get_thought_action(self):
        return self.log
    
    def get_execution_measure(self):
        return self.execution_measure

    def __str__(self):
        s = "FINAL_ANSWER=>" + "\n"
        s += " - NORMAL_FINISH: " + str(self.get_finish()) + "\n"
        s += " - FULL_RESPONSE: " + str(self.get_answer()) + "\n"
        s += " - EXECUTION_JOURNEY: " + "\n"
        s += self.execution_journey.__str__() + "\n"
        s += " - EXCECUTION_MEASURE => " + "\n"
        s += self.execution_measure.__str__() + "\n"        
        s += " - EXCECUTION_EXCEPTION => " + "\n"
        s += self.execution_error.__str__() + "\n"
        return s
    

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
        self.context_values.set_examples(TemplateBank.REACT_DOC_STORE_JOINT_ACTION)
        # journey
        self.execution_journey = ExecutionJourney()
        self.execution_error = ExecutionError()
        self.execution_measure = ExecutionMeasure()

    def invoke(self, user_query):
        self.context_values.set_question(user_query)
        remain_iterations = self.max_iterations

        while remain_iterations > 0:
            try:
                agent_step, observation = None, None
                is_hallucination = False
                self.context_values.set_history(self.llm_agent.get_memory().__str__())
                self.context_values.set_scratchpad(self.execution_journey)
                agent_start = time.time()
                agent_step, input_len, output_len = self.llm_agent.invoke(self.context_values)
                agent_end = time.time()
                tool_start, tool_end = 0, 0

                if isinstance(agent_step, AgentAction):
                    tool_name, tool_input = agent_step.tool, agent_step.tool_input
                    if tool_name in ToolFactory().tool_names(self.agent_tools):
                        tool = [t for t in self.agent_tools if t.name==tool_name][0]
                        tool_start = time.time()
                        observation = tool.func(tool_input)
                        tool_end = time.time()                        
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
                    else:
                        is_hallucination = True

                self.execution_measure.add_iteration(is_hallucination, input_len, output_len,
                                                     agent_end-agent_start, tool_end-tool_start)

                if isinstance(agent_step, AgentFinish):
                        self.execution_journey.add_step(agent_step, "EXECUTION_DONE") 
                        final = FinalAnswer(agent_step, self.execution_journey, 
                                            self.execution_error, self.execution_measure)
                        self.llm_agent.get_memory().message_exchange(user_query, final.get_answer())             
                        return final

                self.execution_journey.add_step(agent_step, observation)                

            except Exception as e:
                self.execution_error.error_input(str(e), input)

            remain_iterations-=1
            if remain_iterations == 0:
                if self.is_verbose:
                    print("TIMEOUT...")
                return FinalAnswer(None, self.context_values.get_scratchpad(), 
                                   self.execution_error, self.execution_measure)

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