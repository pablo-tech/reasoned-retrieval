from helper_suql import ContextParser, InferenceParser, WholisticParser
from domain_knowledge import GiftDataset2, TvDataset, AcDataset
    

class GiftOracle():

    def __init__(self, n,                 
                 completion_llm):
        domain_name="CLIQ"
        domain_datasets=[GiftDataset2()]
        picked_columns=['id', 'price', 
                        'brand', 'colors',
                        'category', 'store', 'gender',
                        'title', 'description',]
        primary_key='id'
        price_column = 'price'
        summarize_columns=['title', 'description']
        self.context_parser = ContextParser(n, domain_name, domain_datasets, 
                picked_columns, primary_key, price_column, 
                completion_llm, is_verbose=False)
        self.inference_parser = InferenceParser(n, domain_name, domain_datasets, 
                picked_columns, primary_key, price_column, summarize_columns,  
                completion_llm, is_verbose=False)
        self.wholistic_parser = WholisticParser(self.context_parser, self.inference_parser)

    def get_context_parser(self):
        return self.context_parser

    def get_inference_parser(self):
        return self.inference_parser

    def get_wholistic_parser(self):
        return self.wholistic_parser

    def get_db_cursor(self):
        return self.context_parser.get_db_cursor()


class ProductRetriever():

    def __init__(self):
        pass


class ProductReader():

    def __init__(self):
        pass    