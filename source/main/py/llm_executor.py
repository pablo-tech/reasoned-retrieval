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

    def get_answer(self):
        return self.answer
    
    def get_success(self):
        return self.is_success

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
                 is_verbose=True):
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
                parsed, observation = None, None
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
                        if self.is_verbose:
                            print(self.tool_observation(tool_name, tool_input, observation))

                if isinstance(parsed, AgentFinish):
                        agent_answer = parsed
                        self.executor_input.add_step(parsed, "EXECUTION_DONE") 
                        final = FinalAnswer(agent_answer, self.executor_input.get_steps(), self.error_log)
                        self.llm_agent.get_memory().message_exchange(user_query, final.get_answer())             
                        return final

            except Exception as e:
                error = str(e)
                observation = error
                self.error_log.append((self.executor_input.str_values(), error))

            self.executor_input.add_step(parsed, observation)                

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
    
    def get_agent(self):
        return self.llm_agent
