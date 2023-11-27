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
                    except Exception as e:
                        # print("STRS_ERROR=" + str(e))
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
                        if isinstance(value, bool):
                            enum_vals[col].add(True)
                            enum_vals[col].add(False)
                        elif len(str(value).split(" ")) <= 3:
                            enum_vals[col].add(value.lower())
                    except Exception as e:
                        # print("ENUM_ERROR="+str(e))
                        pass
        return { k: v for k, v in enum_vals.items()
                 if len(v) > 1 }    

    def legal_product(product_in, n=2):
        product_out = {}
        for k, v in product_in.items():
            k = DataTransformer.legal_key(k)
            if len(k.split("_")) < n:
                product_out[k] = v # .lower()
        try:
            del product_out["case"]
        except:
            pass
        return product_out

    def legal_key(key):
        key = key.replace(":", "_")
        key = key.replace("+", "_")
        key = key.replace(",", "_")
        key = key.replace("|", "_")
        key = key.replace("/", "_")
        key = key.replace("&", "_")
        key = key.replace("__", "_")
        key = key.replace("-", "_")
        key = key.replace("(", "_") 
        key = key.replace(")", "_") 
        key = key.replace("%", "percent") 
        key = key.replace(".", "") 
        if key[0].isdigit():
            key = "n_" + key   
        return key.lower()        


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

    def db_execute(self, query):
        return self.db_cursor.execute(query)
    
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
        results = []
        for invocation in product_parser.get_invocations():
            subdomain_name, columns, schema_sql, enum_values, get_fewshot_examples = invocation
            # enum_values = self.reduced_enums(enum_values)
            # print("INVOKE_COLS=>"+str(columns))
            # print("INVOKE_ENUM=>"+str(enum_values))
            # print("INVOKE_SCHEMA=>"+str(schema_sql))
            prompt = self.get_prompt(query_english, schema_sql, 
                                     enum_values, get_fewshot_examples)
            print(subdomain_name + " PROMPT_LENGTH=" + str(len(prompt)))            
            query_sql = self.run_inference(prompt)
            response = self.db_cursor.execute(query_sql)
            response = self.new_response(query_sql,
                                         columns,
                                         [row for row in response])
            results.extend(response)
        return results[:n]
    
    # def reduced_enums(self, enum_values, n=15):
    #     return { k:v for k, v in enum_values.items() 
    #             if len(v) > n }
    
    def new_response(self, query_sql, result_columns, result_rows):
        user_state, is_success = self.user_state(query_sql)
        if is_success:
            result_items = self.response_items(result_columns, result_rows)
        else:
            result_items = list(result_rows[0])
        return { "user_state": user_state,
                 "result_items": result_items }
    
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
                    if "is_" in key:
                        if value == '1':
                            value = True
                        else:
                            value = ''
                    if value != '':
                        item[key] = value
                i+=1
            items.append(item)
        return items
    
    def user_state(self, query_sql):
        try:
            state = query_sql.split("WHERE")[1].strip()
            state = self.simple_name(state)
            return state, True
        except:
            state = query_sql.split("FROM")[0].strip()
            return state, False
    
    def simple_name(self, column_name):
        column_name = column_name.replace("context.", "")
        column_name = column_name.replace("inference.", "")
        column_name = column_name.replace(";", "")
        return column_name
            
    def get_prompt(self, question, schema_sql, enum_values, get_fewshot_examples):
        prompt = "You are an AI expert semantic parser."
        prompt += "Your task is to generate a SQL query string for the provided question." + "\n"
        prompt += "The database to generate the SQL for has the following signature: " + "\n"  
        prompt += f"{schema_sql}" 
        prompt += "Note that table columns take the following enumerated values:" + "\n"
        for column, values in enum_values.items():
            prompt += f"{column} => {values}" + "\n"
        prompt += "Importantly, you must adjust queries for any possible question mispellings."
        prompt += "EXAMPLES:" + "\n"
        prompt += f"{get_fewshot_examples}" + "\n"
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
        self.sub_domain = 'sub_domain'
            
    def invoke(self, products_in):
        products_out= []
        i = 0
        for product_in in products_in:
            product_out = {}
            try:
                product_out[self.primary_key] = product_in[self.primary_key]
                product_out[self.sub_domain] = product_in[self.sub_domain]
                inferred_tags = self.run_inference(self.get_prompt(self.get_product_str(product_in)))
                for summary_value in eval(inferred_tags):
                    tag = DataTransformer.fil_col(summary_value[0])
                    value = summary_value[1]
                    product_out[tag] = value
                    if self.is_verbose:
                        print(str(i) + "/" + str(len(products_in)) + "\t" + "summary_value="+str(summary_value))
                products_out.append(product_out)    
            except Exception as e:
                pass                
            if i%25 == 0:
                print("summary_inference... " + str(i))
            i+=1
        
        products_out = [DataTransformer.legal_product(p) for p in products_out]
        return products_out 
    
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
    