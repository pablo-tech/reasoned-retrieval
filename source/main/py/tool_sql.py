from helper_suql import DatasetSchema
from domain_knowledge import GiftDataset, GiftDataset2, TvDataset, AcDataset


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
        products, columns = self.product_columns()
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
        products, columns = self.product_columns()
        return self.dataset_schema.create_sql(self.table_name, columns)
    
    def get_enum_values(self):
        return self.dataset_schema.enum_values(self.get_enums(),
                                               self.get_products())
    
    def get_enums(self):
        return self.picked_enums

    def get_table_name(self):
        return self.table_name

    def get_product_columns(self):
        return self.get_products(), self.get_columns()


class ContextLoader(TableLoader):

    def __init__(self, dataset_schema, picked_enums):
        super().__init__(dataset_schema, "CONTEXT")
        self.picked_enums = picked_enums
        self.reduction_products = self.dataset_schema.reduction_products()
        self.reduction_columns = self.dataset_schema.reduction_columns()
            
    def get_fewshot_examples(self):
        return f"""        
Question: what ARISTOCRAT products do you have? 
Answer: SELECT * FROM {self.get_table_name()} WHERE brand = 'Aristocrat';
Question: what GESTS products do you have?
Answer: SELECT * FROM {self.get_table_name()} WHERE brand = 'Guess';
Question: what are the cheapest Scharf products?
Answer: SELECT * FROM {self.get_table_name()} WHERE brand = 'Scharf' ORDER BY price ASC;
Question: "what are the cheapest Carpisa watches?"
Answer: SELECT * FROM {self.get_table_name()} WHERE brand = 'Carpisa' AND title LIKE '%watch%' ORDER BY price ASC;
Question: "What is GW0403L2?"
Answer: SELECT * FROM {self.get_table_name()} WHERE title LIKE '%GW0403L2%';
Question: "Bags for men?"
Answer: SELECT * FROM {self.get_table_name()} WHERE title LIKE '%bag%' AND title NOT LIKE '%women%';
Question: "Glassses for women?"
Answer: SELECT * FROM {self.get_table_name()} WHERE title LIKE '%glass%' AND title NOT LIKE '% men%';
"""
    
    def get_products(self):
        return self.reduction_products

    def get_columns(self):
        return self.reduction_columns
    
    
class InferenceLoader(TableLoader):

    def __init__(self, dataset_schema, picked_enums): 
        super().__init__(dataset_schema, "INFERENCE")
        self.picked_enums = picked_enums
        self.augmentation_columns = self.dataset_schema.augmentation_columns()
        self.augmentation_products = self.dataset_schema.augmentation_products()

    def get_fewshot_examples(self):
        return f"""        
Question: what types of products do you have? 
Answer: SELECT * FROM {self.get_table_name()} WHERE product_types = 'backpack';
Question: what 22 ltrs backpacks do you have?
Answer: SELECT * FROM {self.get_table_name()} WHERE product_size = 'Guess';
Question: what 2 wheel trolleys do your products have?
Answer: SELECT * FROM {self.get_table_name()} WHERE product_wheel_type = '2 wheel';
"""

    def get_products(self):
        return self.augmentation_products

    def get_columns(self):
        return self.augmentation_columns
    

class GiftLoader():

    def __init__(self, n, 
                 completion_llm):
        self.dataset_schema = DatasetSchema(n,
                                            domain_name="CLIQ",
                                            domain_datasets=[GiftDataset2()],
                                            picked_columns=['id', 'price', 
                                                            'brand', 'colors',
                                                            'category', 'store', 'gender',
                                                            'title', 'description',],
                                            primary_key='id',
                                            summarize_columns=['title', 'description'],
                                            completion_llm=completion_llm)
        self.context_loader = ContextLoader(self.dataset_schema, 
                                            picked_enums=['brand', 'colors', 
                                                          'category', 'store', 'gender'])
        self.inference_loader = InferenceLoader(self.dataset_schema, 
                                                picked_enums=['product_brand', 'product_color',
                                                              'product_type', 'product_capacity',
                                                              'product_size', 'product_feature'])

    def get_dataset_schema(self):
        return self.dataset_schema

    def get_context_loader(self):
        return self.context_loader

    def get_inference_loader(self):
        return self.inference_loader


class ProductRetriever():

    def __init__(self):
        pass


class ProductReader():

    def __init__(self):
        pass    