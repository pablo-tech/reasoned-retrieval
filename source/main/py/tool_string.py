from langchain.agents import tool

from llm_run import ModelRun


class StringAnswer(ModelRun):

    def __init__(self):
        super().__init__()


@tool
def get_word_length(word):
    """Returns the length of a word."""
    return len(word)


class StringToolFactory():

    def get_tools():
        return [get_word_length]
