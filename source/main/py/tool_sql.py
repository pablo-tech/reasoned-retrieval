from helper_suql import DatabaseSchema, ContextLoader, InferenceLoader
from domain_knowledge import GiftDataset, GiftDataset2, TvDataset, AcDataset


class GiftLoader():

    def __init__(self, n, 
                 completion_llm):
        self.database_schema = DatabaseSchema(domain_name="CLIQ",
                                              domain_datasets=[GiftDataset2()],
                                              picked_columns=['id', 'price', 
                                                              'title', 'description',
                                                              'brand', 'colors',
                                                              'category', 'store', 'gender'],
                                              primary_key='id',
                                              summarize_columns=['title', 'description'],
                                              completion_llm=completion_llm)
        self.products = self.set_products(n)
        self.context_loader = ContextLoader(self.database_schema, 
                                            self.products,
                                            picked_enums=['brand', 'colors', 
                                                          'category', 'store', 'gender'])
        self.inference_loader = InferenceLoader(self.database_schema, 
                                                self.products,
                                                picked_enums=['product_brand', 'product_color',
                                                              'product_type', 'product_capacity',
                                                              'product_size', 'product_feature'])

    def set_products(self, n):
        products = self.database_schema.get_domain_products()
        if n is not None:
            products = products[:n]
        return products
    
    def get_products(self):
        return self.products
    

class ProductRetriever():

    def __init__(self):
        pass


class ProductReader():

    def __init__(self):
        pass    