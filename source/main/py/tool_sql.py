from helper_suql import DatasetSchema, ContextLoader, InferenceLoader
from domain_knowledge import GiftDataset, GiftDataset2, TvDataset, AcDataset


class GiftLoader():

    def __init__(self, n, 
                 completion_llm):
        self.dataset_schema = DatasetSchema(domain_name="CLIQ",
                                            domain_datasets=[GiftDataset2()],
                                            picked_columns=['id', 'price', 
                                                            'brand', 'colors',
                                                            'category', 'store', 'gender',
                                                            'title', 'description',],
                                            primary_key='id',
                                            summarize_columns=['title', 'description'],
                                            completion_llm=completion_llm)
        self.products = self.set_products(n)
        self.context_loader = ContextLoader(self.dataset_schema, 
                                            self.products,
                                            picked_enums=['brand', 'colors', 
                                                          'category', 'store', 'gender'])
        self.inference_loader = InferenceLoader(self.dataset_schema, 
                                                self.products,
                                                picked_enums=['product_brand', 'product_color',
                                                              'product_type', 'product_capacity',
                                                              'product_size', 'product_feature'])

    def set_products(self, n):
        products = self.dataset_schema.get_domain_products()
        if n is not None:
            products = products[:n]
        return products
    
    def get_products(self):
        return self.products
    
    def get_context_loader(self):
        return self.context_loader

    def get_inference_loader(self):
        return self.inference_loader
    
    def get_dataset_schema(self):
        return self.dataset_schema


class ProductRetriever():

    def __init__(self):
        pass


class ProductReader():

    def __init__(self):
        pass    