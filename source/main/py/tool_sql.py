from domain_product import GiftDataset, TvDataset, AcDataset, DomainIngestion, DatasetValidation


class ProductLoader():

    def __init__(self, db_cursor, completion_llm, is_verbose):
        self.db_cursor = db_cursor
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose
        self.create_schema("CROMA", [TvDataset(), AcDataset()])
        self.create_schema("CLIQ", [GiftDataset()])
    
    def create_schema(self, domain_name, domain_datasets):
        domain = DomainIngestion(data_sets=domain_datasets,
                                 completion_llm=self.completion_llm,
                                 is_verbose=self.is_verbose)
        name = self.domain_name(domain_name)
        self.db_cursor.execute(f"DROP TABLE IF EXISTS {domain_name};")
        columns = self.column_names()
        create_sql = self.create_table(name, 'id', columns)
        self.db_cursor.execute(create_sql)

    def column_names(self, domain):
        domain_data = domain.get_domain_clean()
        keys = set()
        for subdomain_name in subdomain_data.keys():
            subdomain_data = domain_data[subdomain_name]
            for items in subdomain_data.values():
                keys.add(items.keys())

    def create_table(self, schema_name, primary_key, column_names):
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