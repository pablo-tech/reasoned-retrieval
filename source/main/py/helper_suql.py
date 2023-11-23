from domain_knowledge import SchemaCreator, DomainSchema
from helper_sql import SummaryTagger

import sqlite3

from collections import defaultdict


class DatabaseInstance():
    
    def __init__(self, 
                 database_name="tutorial.db"):
        self.db_connection = sqlite3.connect(database_name)
        self.db_cursor = self.db_connection.cursor()

    def get_db_connection(self):
        return self.db_connection

    def get_db_cursor(self):
        return self.db_cursor


class DatasetReducer():

    def __init__(self, primary_key):
        self.primary_key = primary_key

    def unique_columns(self, column_names):
        return [self.primary_key] + [col for col in column_names 
                                     if col!=self.primary_key]

    def columns(self, picked_columns, domain_columns):
        columns = self.unique_columns(domain_columns)
        reduced = [col for col in columns if col in picked_columns]
        return ColumnTransformer.fill_col(reduced)    

    def product_strs(self, products, all_columns):
        rows = ""
        unique_id = set()
        for product in products:
            if product[self.primary_key] not in unique_id:
              unique_id.add(product[self.primary_key])
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

    def find_enum_values(self, picked_enums, products):
        enum_vals = defaultdict(set)
        for product in products:
            for col in picked_enums:
                try:
                  vals = product[col]
                  enum_vals[col].add(vals)
                except Exception as e:
                  pass
        return enum_vals    


class ColumnTransformer():

    def fill_col(columns):
        return [col.replace(" ", "_") for col in columns]


class DatasetAugmenter():

    def __init__(self, summarize_columns, primary_key,
                 completion_llm, is_verbose):
        self.tagger = SummaryTagger(summarize_columns, primary_key,
                                    completion_llm, is_verbose) 

    def column_products(self, products): 
        columns, products = self.tagger.invoke(products)
        columns = sorted(list(columns.keys()))
        columns = [self.tagger.primary_key] + columns
        return ColumnTransformer.fill_col(columns), products
    

class DatasetSchema(DatabaseInstance):

    def __init__(self, 
                 domain_name, domain_datasets, 
                 picked_columns, primary_key, summarize_columns,
                 completion_llm, is_verbose=False):
        super().__init__()
        self.domain_name = domain_name
        self.domain_datasets = domain_datasets
        self.picked_columns = picked_columns        
        self.primary_key = primary_key
        self.completion_llm = completion_llm     
        self.schema_creator = SchemaCreator(self.get_db_cursor(),
                                            domain_name, domain_datasets, picked_columns,  
                                            completion_llm, is_verbose)
        self.ds_reducer = DatasetReducer(primary_key)
        self.ds_augmenter = DatasetAugmenter(summarize_columns, primary_key,
                                             completion_llm, is_verbose)
    
    def create_sql(self, table_name, column_names):
        return self.schema_creator.create_sql(schema_name=table_name, 
                                              primary_key=self.primary_key, 
                                              column_names=column_names)

    def create_table(self, table_name, column_names):
        self.schema_creator.execute_query(self.create_sql(table_name, column_names))

    def get_domain_name(self):
        return self.schema_creator.get_domain_name()
    
    def get_domain_schema(self):
        return self.schema_creator.get_domain_schema()
    
    def get_domain_products(self):
        return list(self.get_domain_schema().get_clean_products())
    
    def augmentation_column_products(self, products):
        return self.ds_augmenter.column_products(products) 
    
    def reduction_columns(self):
        domain_cols = self.get_domain_schema().column_names()
        return self.ds_reducer.columns(self.picked_columns, domain_cols) 
    
    def enum_values(self, picked_enums, from_products):
        return self.ds_reducer.find_enum_values(picked_enums, 
                                                from_products)

    def get_tuple_strs(self, products, columns):
        return self.ds_reducer.product_strs(products, columns)


class TableLoader():

    def __init__(self, dataset_schema:DatasetSchema, nick_name):
        self.dataset_schema = dataset_schema
        self.nick_name = nick_name
        self.table_name = self.dataset_schema.get_domain_name() + "_" + self.nick_name

    def load_items(self):
        columns, rows, insert_sql = self.prepare_load()
        self.execute_load(columns, insert_sql)
        return columns, rows

    def prepare_load(self):
        products, columns = self.product_columns()
        # print("PRODUCTS=>" + str(products))
        print("COLUMNS=>" + str(columns))
        rows = self.dataset_schema.get_tuple_strs(products, columns)
        print("ROWS=>" + str(rows))
        insert_sql = self.get_sql(self.table_name, rows)
        # print("INSERT_SQL=>"+str(insert_sql))
        return columns, rows, insert_sql

    def execute_load(self, columns, insert_sql):
        self.dataset_schema.create_table(self.table_name, columns)
        self.dataset_schema.get_db_cursor().execute(insert_sql)
        self.dataset_schema.get_db_connection().commit()
    
    def get_sql(self, table_name, table_rows):
        return f"""
INSERT INTO {table_name} VALUES {table_rows}
"""    

    def schema_sql(self):
        products, columns = self.product_columns()
        return self.dataset_schema.create_sql(self.table_name, columns)
    
    def get_enum_values(self):
        return self.dataset_schema.enum_values(self.get_enums(),
                                               self.get_products())
    
    def get_table_name(self):
        return self.table_name


class ContextLoader(TableLoader):

    def __init__(self, dataset_schema, context_products, picked_enums):
        super().__init__(dataset_schema, "CONTEXT")
        self.context_products = context_products
        self.picked_enums = picked_enums
        self.context_columns = self.dataset_schema.reduction_columns()
            
    def get_fewshot_examples(self):
        return f"""        
Question: what ARISTOCRAT products do you have? 
Answer: SELECT * FROM {self.get_table_name()} WHERE brand = 'Aristocrat';
Question: what GESTS products do you have?
Answer: SELECT * FROM {self.get_table_name()} WHERE brand = 'Guess';
Question: what are the cheapest Scharf products?
Answer: SELECT * FROM {self.get_table_name()} WHERE brand = 'Scharf' ORDER BY price ASC;
Question: "what are the cheapest Carpisa watches?"
Answer: SELECT * FROM {self.get_table_name()} WHERE brand = 'Carpisa' AND title LIKE '%watch%' ORDER BY price ASC;
Question: "What is GW0403L2?"
Answer: SELECT * FROM {self.get_table_name()} WHERE title LIKE '%GW0403L2%';
Question: "Bags for men?"
Answer: SELECT * FROM {self.get_table_name()} WHERE title LIKE '%bag%' AND title NOT LIKE '%women%';
Question: "Glassses for women?"
Answer: SELECT * FROM {self.get_table_name()} WHERE title LIKE '%glass%' AND title NOT LIKE '% men%';
"""

    def product_columns(self):
        return self.get_products(), self.get_columns()

    def get_products(self):
        return self.context_products
    
    def get_columns(self):
        return self.context_columns
    
    def get_enums(self):
        return self.picked_enums

    

class InferenceLoader(TableLoader):

    def __init__(self, dataset_schema, context_products, picked_enums):
        super().__init__(dataset_schema, "INFERENCE")
        self.context_products = context_products
        self.picked_enums = picked_enums
        self.augmented_columns, self.augmented_products =\
            self.dataset_schema.augmentation_column_products(self.context_products)

    # def get_enum_values(self):
    #     return self.dataset_schema.enum_values(self.get_enums(),
    #                                            self.get_products())

    def get_fewshot_examples(self):
        return f"""        
Question: what types of products do you have? 
Answer: SELECT * FROM {self.get_table_name()} WHERE product_types = 'backpack';
Question: what 22 ltrs backpacks do you have?
Answer: SELECT * FROM {self.get_table_name()} WHERE product_size = 'Guess';
Question: what 2 wheel trolleys do your products have?
Answer: SELECT * FROM {self.get_table_name()} WHERE product_wheel_type = '2 wheel';
"""

    def product_columns(self):
        return self.get_products(), self.get_columns()

    def get_products(self):
        return self.augmented_products

    def get_columns(self):
        return self.augmented_columns

    def get_enums(self):
        return self.picked_enums
