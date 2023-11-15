from collections import defaultdict

from langchain.chat_models import ChatOpenAI


class RunInference():

    def __init__(self, completion_llm, is_verbose=True):
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose

    def run_inference(self, prompt):
        inferred = self.completion_llm.invoke(prompt)
        if isinstance(self.completion_llm, ChatOpenAI):
            inferred = inferred.content
        inferred = inferred.split("Answer:")[1].strip()
        if self.is_verbose:
            print(inferred)
        return inferred


class SqlSemanticParser(RunInference):

    def __init__(self, db_cursor,
                 query_columns, query_signature, query_enums,
                 completion_llm, is_verbose=True):
        super().__init__(completion_llm, is_verbose)
        self.db_cursor = db_cursor
        self.query_columns = query_columns
        self.query_signature = query_signature
        self.query_enums = query_enums

    def invoke(self, query):
        prompt = self.get_prompt(query, 
                                 self.query_columns,
                                 self.query_signature,
                                 self.query_enums)
        inferred_sql = self.run_inference(prompt)
        response = self.db_cursor.execute(inferred_sql)
        return [row for row in response]
            
    def get_prompt(self, question, columns, signature, enums):
        prompt = "You are an AI expert semantic parser."
        prompt += "Your task is to generate a SQL query string for the provided question." + "\n"
        prompt += f"The only table columns to return are {columns}"
        prompt += "The database to generate the SQL for has the following signature: " + "\n"  
        prompt += f"{signature}" 
        prompt += "Note that table columns take the following enumerated values:" + "\n"
        for column, values in enums:
            prompt += f"{column} => {values}" + "\n"
        prompt += "Importantly, you must adjust queries for any possible question mispellings."
        prompt += "EXAMPLES:" + "\n"
        prompt += """        
Question: what ARISTOCRAT products do you have? 
Answer: SELECT brands, price, title FROM CLIQ WHERE brands = 'Aristocrat';
Question: what GESTS products do you have?
Answer: SELECT brands, price, title FROM CLIQ WHERE brands = 'Guess';
Question: what are the cheapest Scharf products?
Answer: SELECT brands, price, title FROM CLIQ WHERE brands = 'Scharf' ORDER BY price ASC;
Question: "what are the cheapest Carpisa watches?"
Answer: SELECT brands, price, title FROM CLIQ WHERE brands = 'Carpisa' AND title LIKE '%watch%' ORDER BY price ASC;
Question: "What is GW0403L2?"
Answer: SELECT brands, price, title FROM CLIQ WHERE title LIKE '%GW0403L2%';
Question: "Bags for men?"
Answer: SELECT brands, price, title FROM CLIQ WHERE title LIKE '%bag%' AND title NOT LIKE '%women%';
Question: "Glassses for women?"
Answer: SELECT brands, price, title FROM CLIQ WHERE title LIKE '%glass%' AND title NOT LIKE '% men%';

"""
        prompt += f"Question: {question}" + "\n"
        return prompt            


class SummaryTagger(RunInference):

    def __init__(self, completion_llm, is_verbose):
        super().__init__(completion_llm, is_verbose)
            
    def invoke(self, products, text_columns, primary_key):
        product_tags = defaultdict(dict)
        slot_values = defaultdict(set)
        i = 0
        for product in products:
            query = "" # TODO: if too long, summarize
            for column in text_columns:
                if column != primary_key:
                    query += product[column] + "\n"
            prompt = self.get_prompt(query)
            inferred_tags = self.run_inference(prompt)
            for slot_value in eval(inferred_tags):
                slot = slot_value[0]
                value = slot_value[1]
                product_tags[product[primary_key]][slot] = value
                slot_values[slot].add(value)
                if self.s_verbose:
                    print(str(i) + "/" + str(len(products)) + "\t" + "slot_value="+str(slot_value))
        return product_tags, slot_values 
            
    def get_prompt(self, query):
        return f"""
You are an AI expert at asking at formulating brief classifications that can be answered by a text,
as well as identifying the instantiation of that classification.
Respond with a python list of string tuples, where the first value is the category classification,
and the second is the instance.
Examples:
Question: Guess Analog Clear Dial Women's Watch GW0403L2
Answer:
[('product gender', 'for women'), ('product type', 'watch'), ('watch type', 'analog'), ('watch dial type', 'clear'), ('product model', 'GW0403L2'), ('product collection', 'Guess')]
Question: {query}
"""