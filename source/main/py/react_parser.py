from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain.agents.output_parsers import ReActJsonSingleInputOutputParser
from langchain.agents.output_parsers import JSONAgentOutputParser
from langchain.agents.react.output_parser import ReActOutputParser
from langchain.agents.agent import AgentOutputParser
from langchain.schema import OutputParserException
from langchain.schema import AgentAction, AgentFinish

from llm_step import StepTransformer


class OptimisticParser(AgentOutputParser):

    def __init__(self):
        pass

    def parse(self, inferred_txt):
        if inferred_txt != "":            
            parsed = self.get_parsed(inferred_txt)
            if parsed is not None:
                return StepTransformer.get_step(parsed)
        raise OutputParserException("UNABLE_TO_PARSE=" + str(inferred_txt))

    def get_parsed(self, inferred_txt):
        ### missing
        if 'Thought: ' in inferred_txt and\
           'Action: ' not in inferred_txt:
            inferred_txt = inferred_txt.strip().replace("Thought: ", '')        
        ### conversation
        if 'Thought: ' not in inferred_txt and\
           'Action: ' not in inferred_txt:
            stripped_txt = inferred_txt.strip()
            completed_txt = f"Thought: {stripped_txt}\n"
            completed_txt += f"Action: Finish[{stripped_txt}]"
            inferred_txt = completed_txt
        ### is None
        parsed = self.react_single_input_output(inferred_txt)
        if parsed is None:
            parsed = self.react_json_single_input_output(inferred_txt)
        if parsed is None:
            parsed = self.json_output(inferred_txt)
        if parsed is None:
            parsed = self.react_output(inferred_txt)
        ### is NOT None
        if isinstance(parsed, AgentAction) and\
                parsed.tool == 'Message':
            parsed = self.get_finish(parsed.tool_input, inferred_txt)
        if isinstance(parsed, AgentAction) and\
                parsed.tool == '':
            parsed =  AgentAction(tool="Describe", 
                                  tool_input="format",
                                  log=inferred_txt)           
        return parsed         

    def get_finish(self, tool_input, inferred_txt):
        return_values={}
        # print("... interpreted finish for -> " + "tool_input=" + str(tool_input) + " inferred_txt=" + str(inferred_txt))
        return_values['output']=tool_input
        return AgentFinish(return_values=return_values,
                           log=inferred_txt) 

    def react_single_input_output(self, txt):
        try:
            return ReActSingleInputOutputParser().parse(txt)
        except Exception as e:
            # print("ReActSingleInputOutputParser=>"+ str(e))
            return None

    def react_json_single_input_output(self, txt):
        try:
            return ReActJsonSingleInputOutputParser().parse(txt)
        except Exception as e:
            # print("ReActJsonSingleInputOutputParser=>"+ str(e))
            return None

    def json_output(self, txt):
        try:
            return JSONAgentOutputParser().parse(txt)
        except Exception as e:
            # print("JSONAgentOutputParser=>"+ str(e))
            return None

    def react_output(self, txt):
        try:
            return ReActOutputParser().parse(txt)
        except Exception as e:
            # print("JSONAgentOutputParser=>"+ str(e))
            return None


class LangchainParser():

    def __init__(self):
        pass

    def react_single_input_output_single(self):
        action_txt = """
        Thought: I need to instead search High Plains (United States).
        Action: Search
        Action Input: High Plains (United States)
        """

        tool_action = ReActSingleInputOutputParser().parse(action_txt)

        return tool_action.tool, tool_action.tool_input, tool_action.log

    def react_single_input_output_final(self):
        final_txt = """
        Thought: High Plains rise in elevation from around 1,800 to 7,000 ft, so the answer is 1,800 to 7,000 ft.
        Final Answer: 1,800 to 7,000 ft
        """

        agent_action = ReActSingleInputOutputParser().parse(final_txt)

        return agent_action.return_values['output'], tool_action.log

    def react_json_single_input_output_single(self):
        action_txt = """
        Thought: High Plains rise in elevation from around 1,800 to 7,000 ft, so the answer is 1,800 to 7,000 ft.
        Action:
        ```
        {
        "action": "Search",
        "action_input": "Who is Leo DiCaprio's girlfriend?"
        }
        ```
        """
        return ReActJsonSingleInputOutputParser().parse(action_txt)

    def react_json_single_input_output_final(self):
        final_txt = """
        Thought: High Plains rise in elevation from around 1,800 to 7,000 ft, so the answer is 1,800 to 7,000 ft.
        Final Answer: I am Leo DiCaprio's girlfriend
        """

        tool_action = ReActJsonSingleInputOutputParser().parse(final_txt)

        return tool_action.return_values['output'], tool_action.log

    def json_output_single(self):
        action_txt = """
        Thought: It does not mention the eastern sector. So I need to look up eastern sector.
        Action:
        ```
        {
        "action": "Search",
        "action_input": "Who is Leo DiCaprio's girlfriend?"
        }
        ```
        """
        tool_action = JSONAgentOutputParser().parse(action_txt)

        return tool_action.tool, tool_action.tool_input, tool_action.log


    def json_output_final(self):
        final_txt = """
        Thought: It does not mention the eastern sector. So I need to look up eastern sector.
        Action:
        ```
        {
        "action": "Final Answer",
        "action_input": "You are Leo DiCaprio's girlfriend"
        }
        ```
        """

        tool_action = JSONAgentOutputParser().parse(final_txt)

        return tool_action.return_values['output'], tool_action.log

    def react_output_single(self):
        action_txt = """
        Thought: It does not mention the eastern sector. So I need to look up eastern sector.
        Action: Lookup[eastern sector]
        """

        tool_action = ReActOutputParser().parse(action_txt)

        return tool_action.tool, tool_action.tool_input, tool_action.log

    def react_output_final(self):
        final_txt = """
        Thought: It does not mention the eastern sector. So I need to look up eastern sector.
        Action: Finish[Richard Nixon]
        """

        tool_action = ReActOutputParser().parse(final_txt)

        return tool_action.return_values['output'], tool_action.log



