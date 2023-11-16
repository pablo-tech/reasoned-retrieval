from collections import defaultdict

from domain_product import SchemaCreator, DomainSchema
from domain_product import GiftDataset, TvDataset, AcDataset
from helper_sql import SummaryTagger

import sqlite3


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

    def unique_columns(self, schema:DomainSchema):
        return [self.primary_key] + [col for col in schema.column_names() 
                                     if col!=self.primary_key]

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
                  # print("vals=" + str(vals) + " " + str(e))
                  pass
        return enum_vals    


class DatasetAugmenter():

    def __init__(self, summarize_columns, primary_key,
                 completion_llm, is_verbose):
        self.tagger = SummaryTagger(summarize_columns, primary_key,
                                    completion_llm, is_verbose) 

    def column_products(self, products): 
        columns, product_summary = self.tagger.invoke(products)
        columns = sorted(list(columns.keys()))
        columns = [self.tagger.primary_key] + columns
        return columns, product_summary
    

class DatabaseSchema(DatabaseInstance):

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
    
    def get_reduced_columns(self):
        columns = self.ds_reducer.unique_columns(self.get_domain_schema())
        return [col for col in columns if col in self.picked_columns]
    
    def enum_values(self, picked_enums, from_products):
        return self.ds_reducer.find_enum_values(picked_enums, 
                                                from_products)

    def get_tuple_strs(self, products, columns):
        return self.ds_reducer.product_strs(products, columns)

    def get_augmentation_tuples(self, products):
        columns, products = self.ds_augmenter.column_products(products) 
        return products, columns
        
    def get_picked_columns(self):
        return self.picked_columns
    
    def get_picked_enums(self):
        return self.picked_enums
    
    def get_primary_key(self):
        return self.primary_key


class TableLoader():

    def __init__(self, database_schema:DatabaseSchema, nick_name):
        self.database_schema = database_schema
        self.nick_name = nick_name
        self.table_name = self.database_schema.get_domain_name() + "_" + self.nick_name

    def load_items(self):
        columns, rows, insert_sql = self.prepare_load()
        self.execute_load(columns, insert_sql)
        return columns, rows

    def prepare_load(self):
        products, columns = self.product_columns()
        print("PRODUCTS=>" + str(products))
        print("COLUMNS=>" + str(columns))
        rows = self.database_schema.get_tuple_strs(products, columns)
        print("ROWS=>" + str(rows))
        insert_sql = self.get_sql(self.table_name, rows)
        print("INSERT_SQL=>"+str(insert_sql))
        return columns, rows, insert_sql

    def execute_load(self, columns, insert_sql):
        columns = self.fill_col(columns)
        self.database_schema.create_table(self.table_name, columns)
        self.database_schema.get_db_cursor().execute(insert_sql)
        self.database_schema.get_db_connection().commit()
    
    def get_sql(self, table_name, table_rows):
        return f"""
INSERT INTO {table_name} VALUES {table_rows}
"""    

    def schema_sql(self):
        products, columns = self.product_columns()
        columns = self.fill_col(columns)
        return self.database_schema.create_sql(self.table_name, columns)
    
    def fill_col(self, columns):
        return [col.replace(" ", "_") for col in columns]


class ContextLoader(TableLoader):

    def __init__(self, database_schema, context_products):
        super().__init__(database_schema, "CONTEXT")
        self.context_products = context_products
    
    def product_columns(self):
        return self.context_products, self.database_schema.get_reduced_columns()
    
    def get_enum_values(self, picked_enums):
        return self.database_schema.enum_values(picked_enums,
                                                self.context_products)

class InferenceLoader(TableLoader):

    def __init__(self, database_schema:DatabaseSchema, context_products):
        super().__init__(database_schema, "INFERENCE")
        self.context_products = context_products

    def product_columns(self):
        augmented_products, columns = self.database_schema.get_augmentation_tuples(self.context_products)
        return augmented_products, columns

    def get_enum_values(self, picked_enums):
        augmented_products, columns = self.database_schema.get_augmentation_tuples(self.context_products)
        return self.database_schema.enum_values(picked_enums,
                                                augmented_products)


class GiftLoader():

    def __init__(self, n, completion_llm):
        self.database_schema = DatabaseSchema(domain_name="CLIQ",
                         domain_datasets=[GiftDataset()],
                         picked_columns=['id', 'brands', 'colors',
                                         'price', 'title'],
                         primary_key='id',
                         summarize_columns=['title'],
                         completion_llm=completion_llm)
        self.products = self.get_products(n)
        self.context_loader = ContextLoader(self.database_schema, self.products)
        self.inference_loader = InferenceLoader(self.database_schema, self.products)

    def get_products(self, n):
        products = self.database_schema.get_domain_products()
        if n is not None:
            products = products[:n]
        return products
        

class ProductRetriever():

    def __init__(self):
        pass


class ProductReader():

    def __init__(self):
        pass    