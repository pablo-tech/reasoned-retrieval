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

    def product_rows(self, products, all_columns):
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

    def __init__(self, tag_columns, primary_key,
                 completion_llm, is_verbose):
        self.tagger = SummaryTagger(tag_columns, primary_key,
                                    completion_llm, is_verbose) 


    def slot_values(self, products):
        product_tags, tag_values = self.tagger.invoke(products)


class DatabaseSchema(DatabaseInstance):

    def __init__(self, 
                 domain_name, domain_datasets, 
                 picked_columns, picked_enums, primary_key,
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
        tag_columns = []
        self.ds_augmenter = DatasetAugmenter(tag_columns, primary_key,
                                             completion_llm, is_verbose)

    def get_primary_key(self):
        return self.primary_key
    
    def get_schema_creator(self):
        return self.schema_creator

    def get_create_sql(self):
        return self.schema_creator.get_create_sql()
    
    def get_domain_name(self):
        return self.schema_creator.get_domain_name()
    
    def get_domain_schema(self):
        return self.schema_creator.get_domain_schema()
    
    def get_domain_products(self):
        return list(self.get_domain_schema().get_clean_products())
    
    def get_ds_reducer(self):
        return self.ds_reducer

    def get_unique_columns(self):
        return self.ds_reducer.unique_columns(self.get_domain_schema())
    
    def get_enum_values(self):
        return self.ds_reducer.find_enum_values(self.picked_enums, 
                                                self.get_domain_products())

    def get_product_rows(self, columns):
        return self.ds_reducer.product_rows(self.get_domain_products(), columns)

    def get_ds_augmenter(self):
        return self.ds_augmenter
    

class ProductLoader(DatabaseSchema):

    def __init__(self, 
                 domain_name, domain_datasets,
                 picked_columns, picked_enums, primary_key,
                 completion_llm):
        super().__init__(domain_name, domain_datasets,
                         picked_columns, picked_enums, primary_key,
                         completion_llm)
    
    def load_products(self):
        insert_sql = self.load_sql()
        self.get_db_cursor().execute(insert_sql)
        self.get_db_connection().commit()
        return insert_sql        

    def load_sql(self):
        return self.get_sql(self.get_domain_name(), 
                            self.get_rows())   

    def get_rows(self):
        columns = self.get_unique_columns()
        columns = [col for col in columns if col in self.picked_columns]
        print("SELECTED_UNIQUE_COLUMNS=" + str(columns))
        rows = self.get_product_rows(columns)
        # print("ACTUAL_PRODUCT_ROWS=" + str(rows))
        return rows

    def get_sql(self, table_name, product_rows):
        return f"""
INSERT INTO {table_name} VALUES {product_rows}
"""    


class GiftLoader(ProductLoader):

    def __init__(self, completion_llm):
        super().__init__(domain_name="CLIQ",
                         domain_datasets=[GiftDataset()],
                         picked_columns=['id', 'brands', 'colors',
                                        'price', 'title'],
                         picked_enums=['brands', 'colors'],
                         primary_key='id',
                         completion_llm=completion_llm)
        

class ProductRetriever():

    def __init__(self):
        pass


class ProductReader():

    def __init__(self):
        pass    