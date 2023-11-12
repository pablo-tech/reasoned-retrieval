from collections import defaultdict

from domain_product import GiftDataset, TvDataset, AcDataset, DomainSchema


class SchemaCreator():

    def __init__(self, domain_name, domain_datasets,
                 selected_columns,
                 db_cursor, completion_llm, is_verbose):
        self.domain_name = domain_name.upper()
        self.domain_datasets = domain_datasets
        self.selected_columns = selected_columns
        self.db_cursor = db_cursor
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose
        self.domain_schema, self.create_sql = self.create_schema()

    def get_domain_schema(self):
        return self.domain_schema

    def get_create_sql(self):
        return self.create_sql

    def get_domain_name(self):
        return self.domain_name
    
    def create_schema(self):
        domain_schema = DomainSchema(data_sets=self.domain_datasets,
                                     completion_llm=self.completion_llm,
                                     is_verbose=self.is_verbose)
        column_names = [col for col in domain_schema.column_names()
                        if col in self.selected_columns]
        create_sql = self.create_table(self.domain_name, 'id', column_names)
        self.execute_query(self.domain_name, create_sql)
        return domain_schema, create_sql

    def execute_query(self, domain_name, create_sql):
        try:
          self.db_cursor.execute(f"DROP TABLE IF EXISTS {domain_name};")
          self.db_cursor.execute(create_sql)
          if self.is_verbose:
              print(create_sql)
        except Exception as e:
          print("CREATION_ERROR=" + domain_name + " " + str(e) + "\n" + str(create_sql))

    def create_table(self, schema_name, primary_key, column_names):
        column_names = self.non_primary(primary_key, column_names)
        column_names = [",\n" + name + " " + "TEXT NOT NULL" for name in column_names]
        column_names = " ".join(column_names)
        return f"""
    CREATE TABLE {schema_name} (
    {primary_key} TEXT PRIMARY KEY {column_names}
    ) ;
    """

    def non_primary(self, primary_key, column_names):
        return sorted([name for name in column_names if name!=primary_key])
    


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

    def enum_values(self, enum_cols, products):
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


class ProductRetriever():

    def __init__(self):
        pass


class ProductReader():

    def __init__(self):
        pass    