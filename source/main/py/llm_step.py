from langchain.schema import AgentAction, AgentFinish


class InterimStep():

    def __init__(self, action_tool, tool_input, action_log):
        self.action_tool = action_tool
        self.tool_input = tool_input
        self.action_log = action_log

    def get_tool(self):
        return self.action_tool

    def get_input(self):
        return self.tool_input

    def get_log(self):
        return self.action_log
    
    def __str__(self):
        s = "interim_step=> "
        s += "action_tool=" + self.action_tool + " "
        s += "tool_input=" + self.tool_input + " "
        s += "action_log=" + self.action_log + " "
        return s

class FinishStep():

    def __init__(self, action_answer, action_log):
        self.action_answer = action_answer
        self.action_log = action_log

    def get_answer(self):
        return self.action_answer

    def get_log(self):
        return self.action_log

    def __str__(self):
        s = "finish_step=> "
        s += "action_answer=" + self.action_answer + " "
        s += "action_log=" + self.action_log + " "
        return s

class StepTransformer():

    def __init__(self):
        pass    

    def get_step(langchain_step):
        if isinstance(langchain_step, AgentAction):
            return InterimStep(langchain_step.tool,
                               langchain_step.tool_input, 
                               langchain_step.log)
        if isinstance(langchain_step, AgentFinish):
            return FinishStep(langchain_step.return_values['output'],
                                langchain_step.log)
        return None
    