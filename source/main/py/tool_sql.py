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
        self.domain_schema = self.create_schema()

    def get_domain_schema(self):
        return self.domain_schema
    
    def get_domain_name(self):
        return self.domain_name
    
    def create_schema(self):
        schema = DomainSchema(data_sets=self.domain_datasets,
                              completion_llm=self.completion_llm,
                              is_verbose=self.is_verbose)
        column_names = [col for col in schema.column_names()
                        if col in self.selected_columns]
        create_sql = self.create_table(self.domain_name, 'id', column_names)
        self.execute_query(self.domain_name, create_sql)
        return schema

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
    

class ProductRetriever():

    def __init__(self):
        pass


class ProductReader():

    def __init__(self):
        pass    