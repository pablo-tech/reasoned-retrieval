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

    def set_enum_values(picked_enums, products, exclude_columns,
                        min_value_length=1, max_value_spacing=3,
                        min_value_count=1):
        enum_vals = defaultdict(set)
        for product in products:
            for col in picked_enums:
                if col not in exclude_columns:
                    try:
                        value = product[col]
                        if isinstance(value, bool):
                            enum_vals[col].add(True)
                            enum_vals[col].add(False)
                        elif len(str(value).split(" ")) <= max_value_spacing:
                            if len(value) > min_value_length:
                                enum_vals[col].add(value.lower())
                    except Exception as e:
                        # print("ENUM_ERROR="+str(e))
                        pass
        return { k: v for k, v in enum_vals.items()
                 if len(v) > min_value_count }    

    def legal_product(product_in, 
                      n=2, valids=["product"]):
        product_out = {}
        for k, v in product_in.items():
            k = DataTransformer.legal_key(k)
            if len(k.split("_")) <= n:
                # for valid in valids:
                #     if valid in k:
                product_out[k] = v # .lower()
        try:
            del product_out["case"]
        except:
            pass
        # print("product_out=" + str(product_out))
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
        try:
            inferred = self.completion_llm.invoke(prompt)
            if isinstance(self.completion_llm, ChatOpenAI):
                inferred = inferred.content
            if self.is_verbose:            
                print(inferred)
            inferred = self.post_infernece(inferred)
            return inferred
        except Exception as e:
            # print("INFERRENCE_ERROR="+str(e))
            return ""

    def post_infernece(self, inferred):
        if "Answer" in inferred:
            try:
                return inferred.split("Answer:")[1].strip()
            except:
                return inferred.strip()
        if "SQL" in inferred:
            try:
                return inferred.split("SQL Query:")[1].strip()
            except:
                return inferred.strip()            
        return inferred.strip() 


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
    

class ParserQuery(RunInference):

    def __init__(self, completion_llm, db_instance, is_verbose=False):
        super().__init__(completion_llm, is_verbose)
        self.db_instance = db_instance

    def invoke_query(self, query_english, query_limit, invocation):
        user_state, result_items = "", []
        try:
            subdomain_name, columns, schema_sql, enum_values, fewshot_examples = invocation
            prompt = self.get_prompt(query_english, schema_sql, 
                                     enum_values, fewshot_examples)
            print(f"""---> subdomain_name={subdomain_name} prompt={len(prompt)}""")                
            query_sql = self.run_inference(prompt)
            # if len(query_sql.split("WHERE")>1):
            query_sql = query_sql.replace(";", f""" LIMIT {query_limit};""")
            print("QUERY_SQL=>" + str(query_sql))            
            result_rows = self.db_instance.execute_read(query_sql)
            # result_rows = [row for row in result_rows]
            user_state = self.user_state(query_sql)
            result_items = self.response_items(columns, result_rows)
        except Exception as e:
            # print("INVOKE_ERROR=" + str(e) + "... QUERY_SQL=" + str(query_sql))
            pass 

        return user_state, result_items
            
    def response_items(self, result_columns, result_rows):
        # print("RESULT_COLS="+str(result_columns))
        # print("RESULT_ROWS="+str(result_rows))
        result_columns = [self.simple_name(column) for column in result_columns]
        items = []
        for row in result_rows:
            item = {}
            i = 0
            for value in row:
                if value != '':
                    try:
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
                    except Exception as e:
                        print("RESPONSE_ITEMS_ERROR=" + str(e))
                i+=1
            items.append(item)
        return items
    
    def user_state(self, query_sql):
        try:
            state = query_sql.split("WHERE")[1].strip()
            state = state.split("LIMIT")[0].strip()
            state = self.simple_name(state)
            return state
        except:
            return ""
    
    def simple_name(self, column_name):
        column_name = column_name.replace("context.", "")
        column_name = column_name.replace("inference.", "")
        column_name = column_name.replace(";", "")
        return column_name
            
    def get_prompt(self, user_question, schema_sql, enum_values, fewshot_examples):
        prompt = "You are an AI expert semantic parser."
        prompt += "Your task is to generate a SQL query string for the provided question." + "\n"
        prompt += "The database to generate the SQL for has the following signature: " + "\n"  
        prompt += f"{schema_sql}" 
        prompt += "Note that table columns take the following enumerated values:" + "\n"
        prompt += str(enum_values)
        prompt += "Importantly, you must adjust queries for any possible question mispellings."
        prompt += "EXAMPLES:" + "\n"
        prompt += f"{fewshot_examples}" + "\n"
        prompt += f"Question: {user_question}" + "\n"

        if self.is_verbose:
            print("PROMPT=>"+str(prompt))
        return prompt            
            
    def state_items(self, user_state, result_items):
        return {"user_state": user_state,
                "result_items": result_items}        


class SemanticQuery(ParserQuery):    

    def __init__(self, query_limit, invocations, 
                 completion_llm, db_instance, is_verbose=False):
        super().__init__(completion_llm, db_instance, is_verbose)
        self.query_limit = query_limit 
        self.invocations = invocations

    def invoke(self, query_english):
        results = []
        for invocation in self.invocations:
            user_state, result_items =\
                 self.invoke_query(query_english, self.query_limit, invocation)
            results.append(self.state_items(user_state, result_items))
        return results


    