from domain_knowledge import DomainSchema
from helper_parser import SummaryTagger, DataTransformer
from domain_knowledge import GiftSuql

from collections import defaultdict


class SchemaCreator(DomainSchema):

    def __init__(self, domain_name, domain_datasets, 
                 picked_columns, primary_key, price_column, 
                 subdomain_name, subdomain_column,
                 db_instance, completion_llm, is_verbose):
        super().__init__(data_sets=domain_datasets,
                         subdomain_name=subdomain_name,
                         subdomain_column=subdomain_column,
                         completion_llm=completion_llm,
                         is_verbose=is_verbose)
        self.domain_name = domain_name.upper()
        self.domain_datasets = domain_datasets
        self.picked_columns = picked_columns
        self.primary_key = primary_key
        self.price_column = price_column
        self.db_instance = db_instance
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose

    def create_table(self, table_name, column_names):
        self.execute_query(self.create_sql(table_name, column_names))

    def execute_query(self, create_sql):
        try:
          self.db_execute(f"DROP TABLE IF EXISTS {self.domain_name};")
          self.db_execute(create_sql)
          if self.is_verbose:
              print(create_sql)
        except Exception as e:
          print("CREATION_ERROR=" + self.domain_name + " " + str(e) + "\n" + str(create_sql))

    def db_execute(self, query):
        return self.db_instance.db_cursor.execute(query)

    def create_sql(self, table_name, column_names):
        column_txt = ""
        i = 1
        for column in sorted(column_names):
            column_txt += self.column_declaration(column)
            if i!=len(column_names):
                column_txt += ","
            column_txt += "\n"
            i += 1
        return f"""
    CREATE TABLE {table_name} (
    {column_txt}
    ) ;
    """

    def column_declaration(self, column_name):
        if column_name == self.primary_key:
            return f"""{self.primary_key} TEXT PRIMARY KEY"""
        if column_name == self.price_column:
            return f"""{self.price_column} FLOAT NOT NULL"""
        if "is_" in column_name:
            return f"""{column_name} BOOLEAN NOT NULL"""
        return f"""{column_name} TEXT NOT NULL"""

    def non_primary(self, primary_key, column_names):
        return sorted([name for name in column_names if name!=primary_key]) 

    def get_domain_name(self):
        return self.domain_name


class DatasetLoader(SchemaCreator):

    def __init__(self, nick_name, domain_name, domain_datasets,
                 subdomain_name, subdomain_column,  
                 picked_columns, primary_key, price_column, 
                 db_instance, completion_llm, is_verbose=False):
        super().__init__(domain_name, domain_datasets, 
                 picked_columns, primary_key, price_column, 
                 subdomain_name, subdomain_column,
                 db_instance, completion_llm, is_verbose)
        self.nick_name = nick_name
        self.db_instance = db_instance
        self.subdomain_column = subdomain_column

    def table_name(self, domain):
        name = self.get_domain_name() + "_" + self.nick_name 
        if domain != "":
            name += "_" + domain
        return name

    def load_items(self, domain=""):
        columns, products = self.get_columns(), self.get_products()
        print("COLUMNS=>" + str(columns))
        products = self.domain_unique_products(products, domain)
        table_name = self.table_name(domain)
        self.create_table(table_name, columns)  
        self.batch_load(columns, products, table_name)      
        return columns, products
    
    def batch_load(self, columns, products, 
                   table_name, n=25):
        max = len(products)
        fails = 0
        i, j = 0, n
        while i < max:
            if j > max:
                j = max
            batch = products[i:j]
            insert_sql = self.prepare_load(columns, batch, table_name)
            # print("INSERT_SQL=>"+str(insert_sql))
            try:
                self.execute_load(insert_sql)
            except Exception as e:
                print("LOAD_EXCEPTION="+str(table_name)+"\t"+str(e) )
                fails+=1
                pass
            i+=n
            j+=n
        print("FAILURE_COUNT="+str(fails))
    
    def domain_unique_products(self, products_in, domain):
        if domain != "":
            products_in = [p for p in products_in if p[self.subdomain_column]==domain]
        products_out = []
        unique = set()
        for product in products_in:
            if product[self.primary_key] not in unique:
               unique.add(product[self.primary_key])
               products_out.append(product) 
        return products_out

    def prepare_load(self, columns, products, table_name):
        # print("PRODUCTS=>" + str(products))
        rows = DataTransformer.product_strs(products, columns, self.primary_key)
        for chunk in rows.split("\n")[:1]:
            if chunk != "":
                print("ROW=>" + str(chunk))
        insert_sql = self.get_sql(table_name, rows)
        return insert_sql

    def execute_load(self, insert_sql):
        self.db_instance.get_db_cursor().execute(insert_sql)
        self.db_instance.get_db_connection().commit()
    
    def get_sql(self, table_name, table_rows):
        return f"""
INSERT INTO {table_name} VALUES {table_rows}
"""    

    def schema_sql(self, domain):
        return self.create_sql(self.table_name(domain), 
                               self.get_columns())
        
    def get_enums(self):
        return sorted(list(self.get_enum_values().keys()))
 
    def get_enum_values(self):
        return self.enum_values


class DatasetReducer(DatasetLoader):

    def __init__(self, nick_name, domain_name, domain_datasets, 
                 subdomain_column, 
                 picked_columns, primary_key, price_column, summarize_columns,
                 db_instance, completion_llm, is_verbose=False):
        super().__init__(nick_name, domain_name, domain_datasets, 
                         "", subdomain_column, 
                         picked_columns, primary_key, price_column, 
                         db_instance, completion_llm, is_verbose)
        self.summarize_columns = summarize_columns
        self.products = self.get_domain_products()
        self.columns = self.set_columns()
        self.enum_values = self.set_enum_values()

    def set_columns(self):
        columns = [col for col in self.get_domain_columns() 
                   if col in self.picked_columns]
        columns = list(set(columns))
        return DataTransformer.fill_cols(sorted(columns))   
    
    def set_enum_values(self):
        enum_exclude = [col for col in self.get_columns() 
                        if col in self.summarize_columns or col not in self.picked_columns or col == self.primary_key or col == self.price_column]
        return DataTransformer.set_enum_values(self.get_columns(),
                                               self.get_products(),
                                               enum_exclude)        

    def get_columns(self):
        return self.columns
        
    def get_products(self):
        return self.products
    
    def get_enum_values(self):
        return self.enum_values


class ContextParser(DatasetReducer):

    def __init__(self, domain_name, domain_datasets, 
                 subdomain_column,
                 picked_columns, primary_key, price_column, summarize_columns, 
                 db_instance, completion_llm, is_verbose=False):
        super().__init__("CONTEXT", domain_name, domain_datasets, 
                         subdomain_column,
                         picked_columns, primary_key, price_column, summarize_columns,
                         db_instance, completion_llm, is_verbose)

    def get_fewshot_examples(self):
        columns = ", ".join(self.get_columns())
        return f"""        
Question: what ARISTOCRAT products do you have? 
Answer: SELECT {columns} FROM {self.table_name("")} WHERE brand = 'Aristocrat';
Question: what GESTS products do you have?
Answer: SELECT {columns} FROM {self.table_name("")} WHERE brand = 'Guess';
Question: what are the cheapest Scharf products?
Answer: SELECT {columns} FROM {self.table_name("")} WHERE brand = 'Scharf' ORDER BY price ASC;
Question: "what are the cheapest Carpisa watches?"
Answer: SELECT {columns} FROM {self.table_name("")} WHERE brand = 'Carpisa' AND title LIKE '%watch%' ORDER BY price ASC;
Question: "What is GW0403L2?"
Answer: SELECT {columns} FROM {self.table_name("")} WHERE title LIKE '%GW0403L2%';
Question: "Bags for men?"
Answer: SELECT {columns} FROM {self.table_name("")} WHERE title LIKE '%bag%' AND title NOT LIKE '%women%';
Question: "Glassses for women?"
Answer: SELECT {columns} FROM {self.table_name("")} WHERE title LIKE '%glass%' AND title NOT LIKE '% men%';
"""
    

class InferenceLoader(DatasetLoader):

    def __init__(self, is_run_inference, domain_name, domain_datasets,
                 subdomain_name, subdomain_column, 
                 picked_columns, primary_key, price_column,  
                 summarize_columns, column_annotation, 
                 db_instance, completion_llm, is_verbose):
        super().__init__("INFERENCE", domain_name, domain_datasets, 
                         subdomain_name, subdomain_column, 
                         picked_columns, primary_key, price_column, 
                         db_instance, completion_llm, is_verbose)
        self.is_run_inference = is_run_inference
        self.subdomain_name = subdomain_name
        self.column_annotation = column_annotation
        self.primary_key = primary_key
        self.summarize_columns = summarize_columns
        self.summary_tagger = SummaryTagger(summarize_columns, primary_key,
                                            completion_llm, is_verbose)
        self.product_cache = GiftSuql()

    def set_column_products(self, working_products): 
        columns, products = self.summary_column_products(working_products)
        columns, products = self.annotation_column_products(columns, products)
        columns = set(columns)
        columns.add(self.primary_key)
        columns = list(columns)
        return DataTransformer.fill_cols(sorted(columns)), products
        
    def summary_column_products(self, context_products, n=30): 
        inference_products = []
        domain_products = self.product_by_domain(context_products)
        if not self.is_run_inference:
            for subdomain_name in domain_products.keys():
                products = self.product_cache.get_corpus(subdomain_name)
                inference_products.extend(products)
            # context_products = context_products[:n]
        else:
            for subdomain_name, context_products in domain_products.items():
                products = self.summary_tagger.invoke(context_products)
                inference_products.extend(products)
                self.product_cache.save_corpus(subdomain_name, products)
        columns = self.extract_columns(inference_products)
        return columns, inference_products
    
    def product_by_domain(self, products):
        domain_products = defaultdict(list)
        for product in products:
            domain_products[product[self.subdomain_column]].append(product)
        return domain_products
    
    def extract_columns(self, products):
        columns = set()
        for product in products:
            columns.update(list(product.keys()))
        return list(columns)
    
    def annotation_column_products(self, columns, products):
        groupings = self.column_annotation.values()
        for grouping in groupings:
            for concept, values in grouping.items():
                concept = "is_" + concept
                columns.append(concept)
                for value in values:
                    for product in products:
                        if value in product[self.subdomain_column]:
                            product[concept] = True
                        else:
                            product[concept] = False
        return columns, products


class InferenceDomain(InferenceLoader):
    
    def __init__(self, is_run_inference, domain_name, domain_datasets,
                 subdomain_name, subdomain_column, 
                 picked_columns, primary_key, price_column, summarize_columns,
                 column_annotation, db_instance, 
                 completion_llm, is_verbose):
        super().__init__(is_run_inference, domain_name, subdomain_name, domain_datasets,
                 picked_columns, primary_key, price_column, subdomain_column, 
                 summarize_columns, column_annotation, 
                 db_instance, completion_llm, is_verbose)
        self.subdomain_column = subdomain_column
        self.inference_columns, self.inference_products =\
                self.augmentation_column_products()
        self.enum_values = self.set_enum_values()

    def get_products(self):
        return self.inference_products

    def get_columns(self):
        return self.inference_columns    
    
    def augmentation_column_products(self):
        subdomain_products = self.get_domain_products()
        columns, products_in = self.set_column_products(subdomain_products) 
        products_out = []
        for product in products_in:
            try:
                if product[self.subdomain_column] == self.subdomain_name:
                    products_out.append(product)
            except Exception as e:
                print("SUBDOMAIN_ERROR="+str(e)+"\t"+str(product))
        return columns, products_out
        # print("subdomain_column=>" + str(self.subdomain_column) + "\t" + str(self.subdomain_name))
    
    def set_enum_values(self):
        enum_exclude = [col for col in self.get_columns() 
                        if col in self.summarize_columns or col == self.primary_key or col == self.price_column]
        return DataTransformer.set_enum_values(self.get_columns(),
                                               self.get_products(),
                                               enum_exclude)        


class InferenceParser():

    def __init__(self, is_run_inference, domain_name, domain_datasets, 
                 subdomain_names, subdomain_column,
                 picked_columns, primary_key, price_column,  
                 summarize_columns, column_annotation, 
                 db_instance, completion_llm, is_verbose=False): 
        self.domain_inference = {}
        for subdomain_name in subdomain_names:
            domain_inference = InferenceDomain(is_run_inference, domain_name, domain_datasets, 
                                               subdomain_name, subdomain_column,
                                               picked_columns, primary_key, price_column,  
                 summarize_columns, column_annotation, 
                 db_instance, completion_llm, is_verbose)
            self.domain_inference[subdomain_name] = domain_inference

    def get_fewshot_examples(self):
        columns = ", ".join(self.get_columns())
        return f"""        
Question: what types of backpacks do you have? 
Answer: SELECT {columns} FROM {self.get_table_name()} WHERE product_types = 'backpack';
Question: what 22 litter backpacks do you have?
Answer: SELECT {columns} FROM {self.get_table_name()} WHERE product_size = '22 ltrs';
Question: what 2 wheel trolleys do your products have?
Answer: SELECT {columns} FROM {self.get_table_name()} WHERE product_wheel_type = '2 wheel';
"""


class WholisticParser():

    def __init__(self, context_parser, inference_parser):
        self.context_parser = context_parser
        self.inference_parser = inference_parser

    def schema_sql(self):
        return f"""
{self.context_parser.schema_sql()}

{self.inference_parser.schema_sql()}
"""
    def get_table_name(self):
        return f"""
{self.context_parser.get_table_name()} AS context JOIN
{self.inference_parser.get_table_name()} AS inference 
ON context.id = inference.id
""".replace("\n", " ")        

    def get_enum_values(self):
        return self.inference_parser.get_enum_values()
        # return { **self.context_parser.get_enum_values(), 
        #          **self.inference_parser.get_enum_values() }

    def get_fewshot_examples(self):
        columns = self.get_columns()
        columns = ", ".join(columns)
        return f"""        
Question: what backpacks do you have? 
Answer: SELECT {columns} FROM {self.get_table_name()} WHERE inference.product_type = 'backpack';
Question: what 22 liter backpacks do you have?
Answer: SELECT {columns} FROM {self.get_table_name()} WHERE inference.product_size = '22 Ltrs';
Question: what color trolleys do your products have?
Answer: SELECT DISTINCT product_color FROM {self.get_table_name()} WHERE inference.product_type = 'duffle trolley bag';
"""

    def get_columns(self):
        columns = ["context.id", "context.price", "context.title"] 
        columns += ["inference."+col for col in self.inference_parser.get_enums()]
        return columns    

