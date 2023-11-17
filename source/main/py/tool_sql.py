from helper_suql import DatabaseSchema, ContextLoader, InferenceLoader
from domain_product import GiftDataset, TvDataset, AcDataset


class GiftLoader():

    def __init__(self, n, 
                 completion_llm):
        self.database_schema = DatabaseSchema(domain_name="CLIQ",
                         domain_datasets=[GiftDataset()],
                         picked_columns=['id', 'brands', 'colors',
                                         'price', 'title'],
                         primary_key='id',
                         summarize_columns=['title'],
                         completion_llm=completion_llm)
        self.products = self.set_products(n)
        self.context_loader = ContextLoader(self.database_schema, 
                                            self.products,
                                            picked_enums=['brands', 'colors'])
        self.inference_loader = InferenceLoader(self.database_schema, 
                                                self.products,
                                                picked_enums=['product_brand', 'product_color'])

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