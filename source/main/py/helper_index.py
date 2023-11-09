class JsonLlmFlatner():
    
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
Your response must be in the format of a python list, not bullets.
What {objective_txt} are present in the question?
"""
    
    def noun_examples(self):
        return """
Question: Wenger by Victorinox Black MOD City Medium Backpack
Answer: ['Wenger', 'Victorinox', 'Black', 'MOD', 'City', 'Medium', 'Backpack'] 
"""

    def adjective_examples(self):
        return """
Question: Victorinox Burgundy Altmont Classic Deluxe Medium Laptop Backpack
Answer: ['Burgundy', 'Classic', 'Deluxe', 'Medium']
"""

    def quantified_examples(self):
        return """
Question: Skybags 35 Ltrs Black Medium Laptop Backpack
Answer: ['35 Ltrs'] 
Question: INSIGNIA 32-inch Class F20 Series Smart HD 720p Fire TV with Alexa Voice Remote (NS-32F201NA23, 2022 Model)
Answer: ['32-inch', 'F20 Series', '2022 Model'] 
Question: Amazon Basics Window Mounted Air Conditioner with Mechanical Control Cools 150 Square Feet, 5000 BTU, AC Unit, White
Answer: ['150 Square Feet', '5000 BTU'] 
"""

    def objective_summary(self, item_txt, examples_txt, objective_txt):
        context = self.system_instruction(objective_txt) + "\n" 
        context += examples_txt + "\n"
        context += "Question: " + item_txt + "\n" 
        context += "Answer: "
        return self.completion_llm.invoke(context)

    def noun_summary(self, item_txt):
        examples_txt = self.noun_examples()
        return self.objective_summary(item_txt, examples_txt, "nouns")
    
    def adjective_summary(self, item_txt):
        examples_txt = self.adjective_examples()
        return self.objective_summary(item_txt, examples_txt, "adjectives")
    
    def quantified_summary(self, item_txt):
        examples_txt = self.quantified_examples()
        return self.objective_summary(item_txt, examples_txt, "quantified values")
