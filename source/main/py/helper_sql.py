class SqlHelper():

    def __init__(self, db_cursor,
                 query_columns, query_signature, query_enums,
                 completion_llm):
        self.db_cursor = db_cursor
        self.query_columns = query_columns
        self.query_signature = query_signature
        self.query_enums = query_enums
        self.completion_llm = completion_llm

    def get_result(self, query, n=3):
        prompt = self.get_prompt(query, 
                                 self.query_columns,
                                 self.query_signature,
                                 self.query_enums)
        sql = self.completion_llm.invoke(prompt)
        return self.db_cursor.execute(sql.content)
            
    def get_prompt(self, question, columns, signature, enums):
        prompt = "You are an AI expert semantic parser."
        prompt += "Your task is to generate a SQL query string for the provided question." + "\n"
        prompt += f"Question: {question}" + "\n"
        prompt += "The database to generate the SQL for has the following signature: " + "\n"  
        prompt += f"The only columns to return are {columns}"
        prompt += f"{signature}" 
        prompt += "Note that table columns take the following enumerated values:" + "\n"
        for column, values in enums:
            prompt += f"{column} => {values}" + "\n"
        return prompt            
