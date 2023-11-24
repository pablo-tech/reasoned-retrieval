from helper_suql import ContextParser, InferenceParser
from domain_knowledge import GiftDataset2, TvDataset, AcDataset
    

class GiftData():

    def __init__(self, n,                 
                 completion_llm):
        domain_name="CLIQ"
        domain_datasets=[GiftDataset2()]
        picked_columns=['id', 'price', 
                        'brand', 'colors',
                        'category', 'store', 'gender',
                        'title', 'description',]
        primary_key='id'
        summarize_columns=['title', 'description']
        context_enums = ['brand', 'colors', 'category', 'store', 'gender']
        inference_enums = ['product_brand', 'product_color',
                           'product_type', 'product_capacity',
                           'product_size', 'product_feature']
        self.context_parser = ContextParser(n, domain_name, domain_datasets, 
                 picked_columns, primary_key, summarize_columns, context_enums, 
                 completion_llm, is_verbose=False)
        self.inference_parser = InferenceParser(n, domain_name, domain_datasets, 
                 picked_columns, primary_key, summarize_columns, inference_enums, 
                 completion_llm, is_verbose=False)

    def get_context_parser(self):
        return self.context_parser

    def get_inference_parser(self):
        return self.inference_parser


class ProductRetriever():

    def __init__(self):
        pass


class ProductReader():

    def __init__(self):
        pass    