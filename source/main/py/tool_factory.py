import os

from langchain.tools.render import render_text_description

from tool_search import SearchToolFactory
from tool_math import MathToolFactory
from tool_conversation import ConversationToolFactory


class ToolFactory():
    # https://python.langchain.com/docs/modules/agents/tools/custom_tools

    def __init__(self, is_verbose=True):
        self.is_verbose = is_verbose

    def tool_summaries(cls, tool_set):
        return render_text_description(tool_set)

    def tool_names(cls, tool_set):
        return ", ".join([t.name for t in tool_set])

    def basic_tools(self, completion_llm):
        return MathToolFactory(self.is_verbose).math_tools(completion_llm) +\
            SearchToolFactory(self.is_verbose).serp_search_tools(completion_llm) +\
            ConversationToolFactory(self.is_verbose).conversation_tools(completion_llm)
                    

