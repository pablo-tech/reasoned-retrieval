class RunJourney():

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
    

class RunError():

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
    

class RunMeasure():

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

    def get_iteration_count(self):
        return self.iteration_count
    
    def get_hallucination_count(self):
        return self.hallucination_count

    def get_min_input_len(self):
        try:
            return min(self.input_len)
        except:
            return 0

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

    def get_min_output_len(self):
        try:
            return min(self.output_len)
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

    def get_min_agent_time(self):
        try:
            return min(self.agent_time)
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

    def get_min_tool_time(self):
        try:
            return min(self.tool_time)
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
        s += "\t iteration_count: " + str(self.get_iteration_count()) + "\n"
        s += "\t hallucination_count: " + str(self.get_hallucination_count()) + "\n"
        s += "\t min_input_len: " + str(self.get_min_input_len()) + "\n"        
        s += "\t max_input_len: " + str(self.get_max_input_len()) + "\n"
        s += "\t total_input_len: " + str(self.get_total_input_len()) + "\n"
        s += "\t min_output_len: " + str(self.get_min_output_len()) + "\n"        
        s += "\t max_output_len: " + str(self.get_max_output_len()) + "\n"
        s += "\t total_output_len: " + str(self.get_total_output_len()) + "\n"
        s += "\t min_agent_time: " + "{:.3f}".format(self.get_min_agent_time()) + "\n"        
        s += "\t max_agent_time: " + "{:.3f}".format(self.get_max_agent_time()) + "\n"
        s += "\t total_agent_time: " + "{:.3f}".format(self.get_total_agent_time()) + "\n"
        s += "\t min_tool_time: " + "{:.3f}".format(self.get_min_tool_time()) + "\n"        
        s += "\t max_tool_time: " + "{:.3f}".format(self.get_max_tool_time()) + "\n"
        s += "\t total_tool_time: " + "{:.3f}".format(self.get_total_tool_time())        
        return s