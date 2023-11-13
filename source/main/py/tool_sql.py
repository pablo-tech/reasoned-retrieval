from collections import defaultdict

from domain_product import SchemaCreator
from domain_product import GiftDataset, TvDataset, AcDataset

import sqlite3


class DatasetReducer():

    def __init__(self):
        self.primary_key = 'id'

    def get_primary_key(self):
        return self.primary_key

    def unique_columns(self, schema):
        return [self.get_primary_key()] + [col for col in schema.column_names() 
                                           if col!=self.get_primary_key()]

    def product_rows(self, products, all_columns):
        rows = ""
        unique_id = set()
        for product in products:
            if product[self.get_primary_key()] not in unique_id:
              unique_id.add(product[self.get_primary_key()])
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

    def find_enum_values(self, enum_cols, products):
        enum_vals = defaultdict(set)
        for product in products:
            for col in enum_cols:
                try:
                  vals = product[col]
                  enum_vals[col].add(vals)
                except Exception as e:
                  # print("vals=" + str(vals) + " " + str(e))
                  pass
        return enum_vals    


class DatasetAugmenter(DatasetReducer):

    def __init__(self):
        super().__init__()


class ProductLoader(DatasetAugmenter):

    def __init__(self, 
                 domain_name, domain_datasets,
                 selected_cols, enum_cols,
                 completion_llm,
                 database_name="tutorial.db"):
        super().__init__()
        self.db_connection = sqlite3.connect(database_name)
        self.db_cursor = self.db_connection.cursor()
        self.schema_creator = SchemaCreator(self.db_cursor,
                                            domain_name, domain_datasets, selected_cols,  
                                            completion_llm, False)
        self.selected_cols = selected_cols 
        self.enum_cols = enum_cols        
        self.domain_schema = self.schema_creator.get_domain_schema()
        self.domain_products = self.domain_schema.get_clean_products()
        self.product_enum_values = self.find_enum_values(self.enum_cols, self.domain_products) 

    def get_db_connection(self):
        return self.db_connection

    def get_db_cursor(self):
        return self.db_cursor

    def load_products(self):
        insert_sql = self.load_sql()
        self.db_cursor.execute(insert_sql)
        self.db_connection.commit()
        return insert_sql        

    def load_sql(self):
        return self.get_sql(self.schema_creator.get_domain_name(), 
                            self.get_rows())   

    def get_rows(self):
        columns = self.unique_columns(self.domain_schema)
        columns = [col for col in columns if col in self.selected_cols]
        print("SELECTED_UNIQUE_COLUMNS=" + str(columns))
        rows = self.product_rows(self.domain_products, columns)
        # print("ACTUAL_PRODUCT_ROWS=" + str(rows))
        return rows

    def get_sql(self, table_name, product_rows):
        return f"""
INSERT INTO {table_name} VALUES {product_rows}
"""    

    def get_schema_creator(self):
        return self.schema_creator

    def get_create_sql(self):
        return self.schema_creator.get_create_sql()

    def get_enum_values(self):
        return self.product_enum_values
    
    def get_domain_products(self):
        return list(self.domain_products)


class GiftLoader(ProductLoader):

    def __init__(self, completion_llm):
        super().__init__(domain_name="CLIQ",
                         domain_datasets=[GiftDataset()],
                         selected_cols=['id', 'brands', 'colors',
                                        'price', 'title'],
                         enum_cols=['brands', 'colors'],
                         completion_llm=completion_llm)
        

class ProductRetriever():

    def __init__(self):
        pass


class ProductReader():

    def __init__(self):
        pass    