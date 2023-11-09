

class JsonFlatner():
    
    def __init__(self, completion_llm, is_verbose):
        self.completion_llm = completion_llm
        self.is_verbose =  is_verbose
    
    def summary_instruction(self):
        return """
You are an AI that summarizes complex JSON objects.
"""

    def context_question(self):
        return """
Summarize this product in a flat JSON
"""

    def item_summary(self, item_tx):
        context = self.summary_instruction() + "\n" 
        context += item_tx + "\n" 
        context += self.context_question()
        return self.completion_llm.invoke(context)
