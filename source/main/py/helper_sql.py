from langchain.chat_models import ChatOpenAI


class SqlHelper():

    def __init__(self, db_cursor,
                 query_columns, query_signature, query_enums,
                 completion_llm, is_verbose=True):
        self.db_cursor = db_cursor
        self.query_columns = query_columns
        self.query_signature = query_signature
        self.query_enums = query_enums
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose

    def get_result(self, query, n=3):
        prompt = self.get_prompt(query, 
                                 self.query_columns,
                                 self.query_signature,
                                 self.query_enums)
        inferred_sql = self.completion_llm.invoke(prompt)
        if isinstance(self.completion_llm, ChatOpenAI):
            inferred_sql = inferred_sql.content
        inferred_sql = inferred_sql.split("Answer:")[1].strip()
        if self.is_verbose:
            print(inferred_sql)
        response = self.db_cursor.execute(inferred_sql)
        return [row for row in response][:n]
            
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
Question: "Watches for men?"
Answer: SELECT brands, price, title FROM CLIQ WHERE title LIKE '%watch%' AND title LIKE ' men ';

"""
        prompt += f"Question: {question}" + "\n"
        return prompt            
