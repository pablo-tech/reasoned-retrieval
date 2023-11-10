from domain_product import GiftDataset, TvDataset, AcDataset, DomainSchema


class SchemaCreator():

    def __init__(self, domain_name, domain_datasets,
                 db_cursor, completion_llm, is_verbose):
        self.db_cursor = db_cursor
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose
        self.domain_schema = {}
        self.create_schema(domain_name, domain_datasets)

    def get_domain_schema(self, domain_name):
        return self.domain_schema[domain_name]
    
    def create_schema(self, domain_name, domain_datasets):
        schema = DomainSchema(data_sets=domain_datasets,
                              completion_llm=self.completion_llm,
                              is_verbose=self.is_verbose)
        domain_name = self.domain_name(domain_name)
        create_sql = self.create_table(domain_name, 
                                       'id', 
                                        schema.column_names())
        self.execute_query(domain_name, create_sql)
        self.domain_schema[domain_name] = schema

    def execute_query(self, domain_name, create_sql):
        try:
          self.db_cursor.execute(f"DROP TABLE IF EXISTS {domain_name};")
          self.db_cursor.execute(create_sql)
          print(create_sql)
        except Exception as e:
          print("CREATION_ERROR=" + domain_name + " " + str(e) + "\n" + str(create_sql))

    def create_table(self, schema_name, primary_key, column_names):
        column_names = self.non_primary(primary_key, column_names)
        column_names = sorted(list(column_names))
        column_names = [",\n" + name + " " + "TEXT NOT NULL" for name in column_names]
        column_names = " ".join(column_names)
        return f"""
    CREATE TABLE {schema_name} (
    {primary_key} TEXT PRIMARY KEY {column_names}
    ) ;
    """

    def domain_name(self, domain_name):
        return domain_name.upper()

    def non_primary(self, primary_key, column_names):
        return sorted([name for name in column_names if name!=primary_key])
    

class ProductRetriever():

    def __init__(self):
        pass


class ProductReader():

    def __init__(self):
        pass    