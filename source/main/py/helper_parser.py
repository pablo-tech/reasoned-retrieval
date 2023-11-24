from collections import defaultdict

from langchain.chat_models import ChatOpenAI



class DataTransformer():

    def fil_col(column):
        return column.replace(" ", "_")
    
    def fill_cols(columns):
        return [DataTransformer.fil_col(col) for col in columns]                

    def product_strs(products, all_columns, primary_key):
        rows = ""
        unique_id = set()
        for product in products:
            if product[primary_key] not in unique_id:
              unique_id.add(product[primary_key])
              values = []
              for column in all_columns:
                  value = ''
                  try:
                    value = product[column]
                  except:
                    pass
                  values.append(value)
              if len(rows) == 0:
                  rows += "\n" + str(tuple(values))
              else:
                  rows += ",\n" + str(tuple(values))
        return rows                  

    def set_enum_values(picked_enums, products, exclude_columns):
        enum_vals = defaultdict(set)
        for product in products:
            for col in picked_enums:
                if col not in exclude_columns:
                    try:
                        value = product[col]
                        if len(value.split(" ")) <= 3:
                            enum_vals[col].add(value)
                    except Exception as e:
                        pass
        return { k: v for k, v in enum_vals.items()
                 if len(v) > 1 }    


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

    def __init__(self, 
                 domain_oracle,
                 completion_llm, is_verbose=False):
        super().__init__(completion_llm, is_verbose)
        self.domain_oracle = domain_oracle
        self.db_cursor = self.domain_oracle.get_db_cursor()

    def invoke_context(self, query, n):
        return self.invoke(query, n,
                           self.domain_oracle.get_context_parser())

    def invoke_inference(self, query, n):
        return self.invoke(query, n, 
                           self.domain_oracle.get_inference_parser())

    def invoke_wholistic(self, query, n):
        return self.invoke(query, n, 
                           self.domain_oracle.get_wholistic_parser())

    def invoke(self, query_english, n, product_parser):
        prompt = self.get_prompt(query_english, product_parser)
        query_sql = self.run_inference(prompt)
        # print(product_parser.get_columns())
        # print(query_sql)
        response = self.db_cursor.execute(query_sql)
        return self.new_response(query_sql,
                                 product_parser.get_columns(),
                                 [row for row in response][:n])
    
    def new_response(self, query_sql, result_columns, result_rows):
        return { "user_state": self.user_state(query_sql),
                 "result_items": self.response_items(result_columns, result_rows) }
    
    def response_items(self, result_columns, result_rows):
        result_columns = [self.simple_name(column) for column in result_columns]
        items = []
        for row in result_rows:
            item = {}
            i = 0
            for value in row:
                if value != '':
                    key = result_columns[i]
                    if key == 'price':
                        value = float(value)
                    item[key] = value
                i+=1
            items.append(item)
        return items
    
    def user_state(self, query_sql):
        try:
            state = query_sql.split("WHERE")[1].strip()
            state = self.simple_name(state)
            return state
        except:
            return query_sql
    
    def simple_name(self, column_name):
        column_name = column_name.replace("context.", "")
        column_name = column_name.replace("inference.", "")
        column_name = column_name.replace(";", "")
        return column_name
            
    def get_prompt(self, question, product_parser):
        prompt = "You are an AI expert semantic parser."
        prompt += "Your task is to generate a SQL query string for the provided question." + "\n"
        prompt += "The database to generate the SQL for has the following signature: " + "\n"  
        prompt += f"{product_parser.schema_sql()}" 
        prompt += "Note that table columns take the following enumerated values:" + "\n"
        for column, values in product_parser.get_enum_values().items():
            prompt += f"{column} => {values}" + "\n"
        prompt += "Importantly, you must adjust queries for any possible question mispellings."
        prompt += "EXAMPLES:" + "\n"
        prompt += f"{product_parser.get_fewshot_examples()}" + "\n"
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
            try:
                reduced_product = {}
                reduced_product[self.primary_key] = product[self.primary_key]
                inferred_tags = self.run_inference(self.get_prompt(self.get_product_str(product)))
                for summary_value in eval(inferred_tags):
                    tag = DataTransformer.fil_col(summary_value[0])
                    value = summary_value[1]
                    reduced_product[tag] = value
                    summary_values[tag].add(value)
                    if self.is_verbose:
                        print(str(i) + "/" + str(len(products)) + "\t" + "summary_value="+str(summary_value))
                product_summaries.append(reduced_product)    
            except Exception as e:
                pass                
            if i%25 == 0:
                print("..." + str(i))
            i+=1                
        return summary_values, product_summaries 
    
    def get_product_str(self, product):
        query = "" # TODO: if too long, summarize
        for column in self.summarize_columns:
            if column != self.primary_key:
                query += str(product[column]) + "\n"
        return query
            
    def get_prompt(self, product_str):
        return f"""
You are an AI expert at asking at formulating brief classifications that can be answered by a text,
as well as identifying the instantiation of that classification.
Respond with a python list of double-quoted string tuples, where the first value is the category classification,
and the second is the instance.
EXAMPLES:
Question: Guess Analog Clear Dial Women's Watch GW0403L2
Answer: 
[("product gender", "for women"), ("product type", "watch"), ("watch type", "analog"), ("watch dial type", "clear"), ("product model", "GW0403L2"), ("product collection", "Guess")]
Question: Teakwood Leathers Navy & Red Medium Duffle Bag
Answer: 
[("product brand", "Teakwood Leathers"), ("product color", "navy & red"), ("product size", "medium"), ("product type", "duffle bag")]
Question: Aristocrat 32 Ltrs Green Medium Backpack
Answer: 
[("product brand", "Aristocrat"), ("product capacity", "32 Ltrs"), ("product color", "green"), ("product size", "medium"), ("product type", "backpack")]
Question: {product_str}
"""
    