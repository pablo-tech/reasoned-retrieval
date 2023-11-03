import os

from langchain.tools.render import render_text_description

from tool_search import SearchToolFactory
from tool_math import MathToolFactory
from tool_conversation import ConversationToolFactory


class ToolFactory():
    # https://python.langchain.com/docs/modules/agents/tools/custom_tools

    def __init__(self, completion_llm, is_verbose=True):
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose

    def tool_summaries(cls, tool_set):
        return render_text_description(tool_set)

    def tool_names(cls, tool_set):
        return ", ".join([t.name for t in tool_set])

    def basic_tools(self):
        return MathToolFactory(self.completion_llm, self.is_verbose).math_tools() +\
            SearchToolFactory(self.completion_llm, self.is_verbose).serp_search_tools() +\
            ConversationToolFactory(self.completion_llm, self.is_verbose).conversation_tools()
                    

