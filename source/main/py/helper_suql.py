from domain_knowledge import DomainSchema
from helper_parser import SummaryTagger, ColumnTransformer

from collections import defaultdict


class SchemaCreator(DomainSchema):

    def __init__(self, 
                 domain_name, domain_datasets, 
                 selected_columns, primary_key,
                 completion_llm, is_verbose):
        super().__init__(data_sets=domain_datasets,
                         completion_llm=completion_llm,
                         is_verbose=is_verbose)
        self.domain_name = domain_name.upper()
        self.domain_datasets = domain_datasets
        self.selected_columns = selected_columns
        self.primary_key = primary_key
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose

    def get_domain_name(self):
        return self.domain_name

    def create_table(self, table_name, column_names):
        self.execute_query(self.create_sql(table_name, column_names))

    def execute_query(self, create_sql):
        try:
          self.db_cursor.execute(f"DROP TABLE IF EXISTS {self.domain_name};")
          self.db_cursor.execute(create_sql)
          if self.is_verbose:
              print(create_sql)
        except Exception as e:
          print("CREATION_ERROR=" + self.domain_name + " " + str(e) + "\n" + str(create_sql))

    def create_sql(self, table_name, column_names):
        column_names = self.non_primary(self.primary_key, column_names)
        column_names = [",\n" + name + " " + "TEXT NOT NULL" for name in column_names]
        column_names = " ".join(column_names)
        return f"""
    CREATE TABLE {table_name} (
    {self.primary_key} TEXT PRIMARY KEY {column_names}
    ) ;
    """

    def non_primary(self, primary_key, column_names):
        return sorted([name for name in column_names if name!=primary_key])
    

class DatasetReducer():

    def __init__(self, primary_key, picked_columns):
        self.primary_key = primary_key
        self.picked_columns = picked_columns

    def unique_columns(self, column_names):
        return [self.primary_key] + [col for col in column_names 
                                     if col!=self.primary_key]

    def columns(self, domain_columns):
        columns = self.unique_columns(domain_columns)
        reduced = [col for col in columns if col in self.picked_columns]
        return ColumnTransformer.fill_cols(reduced)    

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


class DatasetAugmenter():

    def __init__(self, summarize_columns, primary_key,
                 completion_llm, is_verbose):
        self.tagger = SummaryTagger(summarize_columns, primary_key,
                                    completion_llm, is_verbose) 

    def column_products(self, products): 
        columns, products = self.tagger.invoke(products)
        columns = sorted(list(columns.keys()))
        columns = [self.tagger.primary_key] + columns
        return ColumnTransformer.fill_cols(columns), products
    

class DatasetSchema(SchemaCreator):

    def __init__(self, n,
                 domain_name, domain_datasets, 
                 picked_columns, primary_key, summarize_columns,
                 completion_llm, is_verbose=False):
        super().__init__(domain_name, domain_datasets, 
                         picked_columns, primary_key,
                         completion_llm, is_verbose)
        self.working_products = self.set_products(n)
        self.domain_name = domain_name
        self.domain_datasets = domain_datasets
        self.picked_columns = picked_columns        
        self.primary_key = primary_key
        self.completion_llm = completion_llm     
        self.ds_reducer = DatasetReducer(primary_key, picked_columns)
        self.ds_augmenter = DatasetAugmenter(summarize_columns, primary_key,
                                             completion_llm, is_verbose)
    
    def set_products(self, n):
        products = self.get_domain_products()
        if n is not None:
            products = products[:n]
        return products
    
    def reduction_products(self):
        return self.working_products

    def reduction_columns(self):
        return self.ds_reducer.columns(self.column_names()) 
    
    def enum_values(self, picked_enums, from_products):
        return self.ds_reducer.find_enum_values(picked_enums, 
                                                from_products)

    def get_tuple_strs(self, products, columns):
        return self.ds_reducer.product_strs(products, columns)

    def augmentation_products(self):
        column, products = self.augmentation_column_products()
        return products

    def augmentation_columns(self):
        column, products = self.augmentation_column_products()
        return column

    def augmentation_column_products(self):
        return self.ds_augmenter.column_products(self.working_products) 


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
        products, columns = self.get_product_columns()
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
        return self.dataset_schema.create_sql(self.get_table_name(), 
                                              self.get_columns())
    
    def get_enum_values(self):
        return self.dataset_schema.enum_values(self.get_enums(),
                                               self.get_products())
    
    def get_enums(self):
        return self.picked_enums

    def get_table_name(self):
        return self.table_name

    def get_product_columns(self):
        return self.get_products(), self.get_columns()