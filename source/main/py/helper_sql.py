from collections import defaultdict

from langchain.chat_models import ChatOpenAI


class ColumnTransformer():

    def fil_col(column):
        return column.replace(" ", "_")
    
    def fill_cols(columns):
        return [ColumnTransformer.fil_col(col) for col in columns]


class RunInference():

    def __init__(self, completion_llm, is_verbose=False):
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose

    def run_inference(self, prompt):
        inferred = self.completion_llm.invoke(prompt)
        if isinstance(self.completion_llm, ChatOpenAI):
            inferred = inferred.content
        if self.is_verbose:            
            print(inferred)
        try:
            inferred = inferred.split("Answer:")[1].strip()
        except: 
            inferred = inferred.strip() 
        # print("INFERRED=" + str(inferred))            
        return inferred


class SqlSemanticParser(RunInference):

    def __init__(self, db_cursor,
                 product_parser,
                 completion_llm, is_verbose=False):
        super().__init__(completion_llm, is_verbose)
        self.db_cursor = db_cursor
        self.product_parser = product_parser

    def invoke(self, query):
        prompt = self.get_prompt(query)
        inferred_sql = self.run_inference(prompt)
        print(self.product_parser.get_columns())
        print(inferred_sql)
        response = self.db_cursor.execute(inferred_sql)
        return [row for row in response]
            
    def get_prompt(self, question):
        prompt = "You are an AI expert semantic parser."
        prompt += "Your task is to generate a SQL query string for the provided question." + "\n"
        prompt += "The database to generate the SQL for has the following signature: " + "\n"  
        prompt += f"{self.product_parser.schema_sql()}" 
        prompt += "Note that table columns take the following enumerated values:" + "\n"
        for column, values in self.product_parser.get_enum_values().items():
            prompt += f"{column} => {values}" + "\n"
        prompt += "Importantly, you must adjust queries for any possible question mispellings."
        prompt += "EXAMPLES:" + "\n"
        prompt += f"{self.product_parser.get_fewshot_examples()}" + "\n"
        prompt += f"Question: {question}" + "\n"

        if self.is_verbose:
            print("PROMPT=>"+str(prompt))
        return prompt            


class SummaryTagger(RunInference):

    def __init__(self, summarize_columns, primary_key,
                 completion_llm, is_verbose):
        super().__init__(completion_llm, is_verbose)
        self.summarize_columns = summarize_columns
        self.primary_key = primary_key
            
    def invoke(self, products):
        product_summaries= []
        summary_values = defaultdict(set)
        i = 0
        for product in products:
            product_summary = {}
            product_summary[self.primary_key] = product[self.primary_key]
            query = "" # TODO: if too long, summarize
            for column in self.summarize_columns:
                if column != self.primary_key:
                    query += product[column] + "\n"
            prompt = self.get_prompt(query)
            inferred_tags = self.run_inference(prompt)
            for summary_value in eval(inferred_tags):
                tag = ColumnTransformer.fil_col(summary_value[0])
                value = summary_value[1]
                product_summary[tag] = value
                summary_values[tag].add(value)
                if self.is_verbose:
                    print(str(i) + "/" + str(len(products)) + "\t" + "summary_value="+str(summary_value))
            product_summaries.append(product_summary)                    
            i+=1
        return summary_values, product_summaries 
            
    def get_prompt(self, query):
        return f"""
You are an AI expert at asking at formulating brief classifications that can be answered by a text,
as well as identifying the instantiation of that classification.
Respond with a python list of string tuples, where the first value is the category classification,
and the second is the instance.
EXAMPLES:
Question: Guess Analog Clear Dial Women's Watch GW0403L2
Answer: 
[('product gender', 'for women'), ('product type', 'watch'), ('watch type', 'analog'), ('watch dial type', 'clear'), ('product model', 'GW0403L2'), ('product collection', 'Guess')]
Question: Teakwood Leathers Navy & Red Medium Duffle Bag
Answer: 
[('product brand', 'Teakwood Leathers'), ('product color', 'navy & red'), ('product size', 'medium'), ('product type', 'duffle bag')]
Question: Aristocrat 32 Ltrs Green Medium Backpack
Answer: 
[('product brand', 'Aristocrat'), ('product capacity', '32 Ltrs'), ('product color', 'green'), ('product size', 'medium'), ('product type', 'backpack')]
Question: {query}
"""