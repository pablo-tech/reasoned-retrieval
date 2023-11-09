import os
import json
    
from langchain.chat_models import ChatOpenAI

from helper_index import JsonFlatner
from domain_corpus import DomainDataset

    
class GiftClean(DomainDataset):

    def __init__(self, n, completion_llm, is_verbose):
        super().__init__(n, dir_path="/content/drive/MyDrive/TataLLM/GiftReader/")
        flatner = JsonFlatner(completion_llm, is_verbose)
        self.clean_data = []
        for item in self.get_raw():  
            clean = flatner.item_summary(str(item))
            if isinstance(completion_llm, ChatOpenAI):
                clean = clean.content
            self.clean_data.append(json.loads(clean))  
        self.data_store = self.get_store()

    def get_clean(self):
        return self.clean_data
    
    def get_store(self):
        return { item['title']: item for item in self.get_clean()}
    
    def get_product(self, title_txt):
        return self.data_store[title_txt]


class GiftRetriever():

    def __init__(self, completion_llm, is_verbose):
        super().__init__(completion_llm, is_verbose)
        self.doc_store = {}

    def subquery(self, query):
        pass
