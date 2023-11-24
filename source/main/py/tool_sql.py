from helper_suql import DatasetSchema
from helper_parser import ContextParser, InferenceParser
from domain_knowledge import GiftDataset2, TvDataset, AcDataset
    

class GiftData():

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
        self.context_parser = ContextParser(self.dataset_schema, 
                                            picked_enums=['brand', 'colors', 
                                                          'category', 'store', 'gender'])
        self.inference_parser = InferenceParser(self.dataset_schema, 
                                                picked_enums=['product_brand', 'product_color',
                                                              'product_type', 'product_capacity',
                                                              'product_size', 'product_feature'])

    def get_dataset_schema(self):
        return self.dataset_schema

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