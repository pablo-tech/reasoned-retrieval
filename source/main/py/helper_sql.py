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
        sql = self.completion_llm.invoke(prompt)
        if isinstance(self.completion_llm, ChatOpenAI):
            sql = sql.content
        if self.is_verbose:
            print(sql)
        response = self.db_cursor.execute(sql)
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
Question: what GUESS products do you have? 
Answer: SELECT brands, price, title FROM CLIQ WHERE brands = 'Guess';
Question: what GESTS products do you have?
Answer: SELECT brands, price, title FROM CLIQ WHERE brands = 'Guess';
Question: what are the cheapest GUESS products?
Answer: SELECT brands, price, title FROM CLIQ WHERE brands = 'Guess' ORDER BY price ASC;
"""
        prompt += f"Question: {question}" + "\n"
        return prompt            
