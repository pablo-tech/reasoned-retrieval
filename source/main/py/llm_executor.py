import time

from react_template import TemplateBank, ReactDescribe
from tool_factory import ToolFactory
from llm_memory import LlmMemory
from llm_agent import AgentFactory
from llm_run import RunAnswer, ModelRun
from llm_step import InterimStep, FinishStep

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

    def set_scratchpad(self, run_journey):
        self.template_vars["agent_scratchpad"] = run_journey.__str__()

    def get_scratchpad(self):
        return self.template_vars["agent_scratchpad"]
    
    def set_history(self, chat_history):
        self.template_vars["chat_history"] = chat_history.__str__()

    def get_history(self):
        return self.template_vars["chat_history"]

    def get_values(self):
        return self.template_vars
    

class ReducedContext(ContextValues):

    def __init__(self):
        super().__init__()


class PipelinedExecutor(ModelRun):
# https://api.python.langchain.com/en/latest/_modules/langchain/agents/agent.html#AgentExecutor

    def __init__(self,
                 llm_agent,
                 max_iterations,
                 max_execution_time,
                 agent_stop=["Observation"],
                 is_verbose=False):
        super().__init__("EXECUTOR")
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

    def invoke(self, user_query):
        self.context_values.set_question(user_query)
        self.new_journey()        
        remain_iterations = self.max_iterations

        while remain_iterations > 0:
            try:
                model_step, observation, prompt_str = None, None, None
                is_hallucination = False
                self.context_values.set_history(self.llm_agent.get_memory().__str__())
                self.context_values.set_scratchpad(self.get_journey())
                model_start = time.time()
                model_step, prompt_str, input_len, output_len = self.llm_agent.invoke(self.context_values)
                model_end = time.time()

                # if self.is_verbose:
                #     print(model_step.__str__().replace("\n", "\t"))

                if isinstance(model_step, InterimStep):
                    tool_name, tool_input = model_step.get_tool(), model_step.get_input()
                    if tool_name in ToolFactory.tool_names(self.agent_tools):
                        tool = [t for t in self.agent_tools if t.name==tool_name][0]
                        tool_run = tool.func(tool_input, user_query)
                        if self.is_verbose:
                            print("TOOL_" + str(tool_run))
                        observation = tool_run.get_answer()
                    elif tool_name == "Describe" and tool_input == 'format':
                        observation = ReactDescribe().react_format() 
                        observation += ReactDescribe().name_template(self.llm_agent.get_tool_names())
                    elif tool_name == "List" and tool_input == 'tools':
                        observation = ReactDescribe().name_template(self.llm_agent.get_tool_names())
                    elif tool_name == "Describe" and tool_input == 'tools':
                        observation = ReactDescribe().summary_template(self.llm_agent.get_tool_summaries())
                    elif tool_name not in ToolFactory.tool_names(self.agent_tools):
                        observation = tool_name + " is not a valid action available to the agent. "
                        observation += "Try: 'Thought: I need to describe the tools available to the agent\nAction: Describe[tools]'."
                        is_hallucination = True

                self.get_measure().add_run(is_hallucination, input_len, output_len,
                                           model_end-model_start)

                if isinstance(model_step, FinishStep):
                        self.get_journey().add_run(model_step, model_step.get_answer()) 
                        final_run = RunAnswer(model_step, self.get_journey(), 
                                              self.get_error(), self.get_measure(), self.get_name())
                        self.llm_agent.get_memory().message_exchange(user_query, final_run.get_answer())             
                        if self.is_verbose:
                            print("\n\n" + str(final_run) + "\n\n")
                        return final_run

                self.get_journey().add_run(model_step, observation)                

            except Exception as e:
                self.get_error().error_input("EXECUTOR_ERROR=" + str(e) + "\nCONTEXT=>" + str(prompt_str), 
                                             observation)


            remain_iterations-=1

            if remain_iterations == 0:
                if self.is_verbose:
                    print("TIMEOUT...")
                timeout_run = RunAnswer(None, self.context_values.get_scratchpad(), 
                                        self.get_error(), self.get_measure(), self.get_name())
                # if self.is_verbose:
                #     print("\n\n" + str(timeout_run) + "\n\n")                
                return timeout_run
            

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
                       agent_tools,
                       agent_memory=LlmMemory(),
                       max_iterations=10,
                       max_execution_time=None):
        ''' ReAct Inference Solve '''
        react_agent = self.agent_factory.react_agent(agent_tools=agent_tools,
                                                     agent_memory=agent_memory)
        return PipelinedExecutor(llm_agent=react_agent,
                                 max_iterations=max_iterations,
                                 max_execution_time=max_execution_time,
                                 is_verbose=self.is_verbose)