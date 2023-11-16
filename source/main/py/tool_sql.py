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
        print("CLEANIFY PRODS" + str(products))
        summary_values, product_summary = self.tagger.invoke(products)
        columns = sorted(list(summary_values.keys()))
        columns = [col.replace(" ", "_") for col in summary_values]
        return columns, product_summary
    

class DatabaseSchema(DatabaseInstance):

    def __init__(self, 
                 domain_name, domain_datasets, 
                 picked_columns, picked_enums, primary_key, summarize_columns,
                 completion_llm, is_verbose=False):
        super().__init__()
        self.domain_name = domain_name
        self.domain_datasets = domain_datasets
        self.picked_columns = picked_columns 
        self.picked_enums = picked_enums           
        self.primary_key = primary_key
        self.completion_llm = completion_llm     
        self.schema_creator = SchemaCreator(self.get_db_cursor(),
                                            domain_name, domain_datasets, picked_columns,  
                                            completion_llm, is_verbose)
        self.ds_reducer = DatasetReducer(primary_key)
        self.ds_augmenter = DatasetAugmenter(summarize_columns, primary_key,
                                             completion_llm, is_verbose)
    
    def create_sql(self, column_names):
        return self.schema_creator.create_sql(schema_name=self.get_domain_name(), 
                                              primary_key=self.primary_key, 
                                              column_names=column_names)

    def create_table(self, column_names):
        self.schema_creator.execute_query(self.create_sql(column_names))

    def get_domain_name(self):
        return self.schema_creator.get_domain_name()
    
    def get_domain_schema(self):
        return self.schema_creator.get_domain_schema()
    
    def get_domain_products(self):
        return list(self.get_domain_schema().get_clean_products())
    
    def get_reduced_columns(self):
        columns = self.ds_reducer.unique_columns(self.get_domain_schema())
        return [col for col in columns if col in self.picked_columns]
    
    def get_enum_values(self):
        return self.ds_reducer.find_enum_values(self.picked_enums, 
                                                self.get_domain_products())

    def get_tuple_strs(self, products, columns):
        return self.ds_reducer.product_strs(products, columns)
        # return products
        # rows = {}
        # for product in products:
        #     rows[product[self.primary_key]] = product
        # return rows


    def get_augmentation_tuples(self, products):
        columns, products = self.ds_augmenter.column_products(products) 
        # rows = {}
        # for product in products:
        #     rows[product[self.primary_key]] = product
        # return rows, columns
        return products, columns
        
    def get_picked_columns(self):
        return self.picked_columns
    
    def get_picked_enums(self):
        return self.picked_enums
    
    def get_primary_key(self):
        return self.primary_key


class TableLoader():

    def __init__(self, database_schema:DatabaseSchema):
        self.database_schema = database_schema

    def load_items(self, n=None):
        columns, insert_sql = self.prepare_load(n)
        self.execute_load(columns, insert_sql)

    def prepare_load(self, n):
        products = self.get_products(n)
        columns = self.get_columns()
        print("COLUMNS=" + str(columns))
        rows = self.database_schema.get_tuple_strs(products, columns)
        print("ROWS=" + str(rows))
        insert_sql = self.get_sql(self.database_schema.get_domain_name(), rows)
        return columns, insert_sql

    def execute_load(self, columns, insert_sql, n=None):
        self.database_schema.create_table(columns)
        self.database_schema.get_db_cursor().execute(insert_sql)
        self.database_schema.get_db_connection().commit()
        print("insert_sql="+str(insert_sql))

    def get_products(self, n):
        products = self.database_schema.get_domain_products()
        print("get_domain_products=" + str(products))
        if n is not None:
            products = products[:n]
        return products
    
    def get_sql(self, table_name, table_rows):
        return f"""
INSERT INTO {table_name} VALUES {table_rows}
"""    

    def schema_sql(self):
        return self.database_schema.create_sql(self.get_columns())


class ContextLoader(TableLoader):

    def __init__(self, database_schema):
        super().__init__(database_schema)
    
    def get_columns(self):
        return self.database_schema.get_reduced_columns()
    

class InferenceLoader(TableLoader):

    def __init__(self, database_schema:DatabaseSchema):
        super().__init__(database_schema)

    def get_columns(self, n=None):
        products = self.get_products(n)
        return []
        # products, columns = self.database_schema.get_augmentation_tuples(products)
        # return columns
    

class GiftLoader(DatabaseSchema):

    def __init__(self, completion_llm):
        super().__init__(domain_name="CLIQ",
                         domain_datasets=[GiftDataset()],
                         picked_columns=['id', 'brands', 'colors',
                                         'price', 'title'],
                         picked_enums=['brands', 'colors'],
                         primary_key='id',
                         summarize_columns=['title'],
                         completion_llm=completion_llm)
        self.context_loader = ContextLoader(self)
        self.inference_loader = InferenceLoader(self)
        

class ProductRetriever():

    def __init__(self):
        pass


class ProductReader():

    def __init__(self):
        pass    