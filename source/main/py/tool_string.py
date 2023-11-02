from langchain.agents import tool


@tool
def get_word_length(word):
    """Returns the length of a word."""
    return len(word)


class StringToolFactory():

    def string_tools():
        return [get_word_length]
