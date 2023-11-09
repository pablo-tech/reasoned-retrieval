

class JsonFlatner():
    
    def __init__(self, completion_llm, is_verbose):
        self.completion_llm = completion_llm
        self.is_verbose =  is_verbose
    
    def summary_instruction(self):
        return """
You are an AI expert at summarizing complex JSON objects.
"""

    def context_question(self):
        return """
Summarize this product into a flat JSON
"""

    def item_summary(self, item_txt):
        context = self.summary_instruction() + "\n" 
        context += item_txt+ "\n" 
        context += self.context_question()
        return self.completion_llm.invoke(context)


class PosExtractor():
    
    def __init__(self, completion_llm, is_verbose):
        self.completion_llm = completion_llm
        self.is_verbose =  is_verbose
    
    def system_instruction(self, objective_txt):
        return f"""
You are an AI expert at extracting {objective_txt} from strings.
"""

    def context_question(self, objective_txt):
        return f"""
What {objective_txt} are present in this text?
"""

    def objective_summary(self, item_txt, objective_txt):
        context = self.system_instruction(objective_txt) + "\n" 
        context += item_txt+ "\n" 
        context += self.context_question(objective_txt)
        return self.completion_llm.invoke(context)

    def noun_summary(self, item_txt):
        return self.objective_summary(item_txt, "nouns")
    
    def adjective_summary(self, item_txt):
        return self.objective_summary(item_txt, "adjectives")
    
    def quantified_summary(self, item_txt):
        return self.objective_summary(item_txt, "quantified values")
