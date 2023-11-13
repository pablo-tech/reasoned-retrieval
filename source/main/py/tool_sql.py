from collections import defaultdict

from domain_product import SchemaCreator
from domain_product import GiftDataset, TvDataset, AcDataset


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


class ProductLoader(DatasetReducer):

    def __init__(self, db_cursor,
                 domain_name, domain_datasets,
                 selected_cols, enum_cols,
                 completion_llm):
        super().__init__()
        self.schema_creator = SchemaCreator(domain_name, domain_datasets, 
                                            selected_cols, db_cursor, 
                                            completion_llm, False)
        self.selected_cols = selected_cols 
        self.enum_cols = enum_cols

    def load_sql(self):
        schema = self.schema_creator.get_domain_schema()
        table_name = self.schema_creator.get_domain_name()
        rows = self.get_rows(schema)
        return self.get_sql(table_name, rows)   

    def get_rows(self, schema):
        products = schema.get_clean_products()
        self.product_enum_values = self.find_enum_values(self.enum_cols, products)
        columns = self.unique_columns(schema)
        columns = [col for col in columns if col in self.selected_cols]
        print("SELECTED_UNIQUE_COLUMNS=" + str(columns))
        rows = self.product_rows(products, columns)
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


class GiftLoader(ProductLoader):

    def __init__(self, db_cursor, completion_llm):
        super().__init__(db_cursor,
                         domain_name="CLIQ",
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