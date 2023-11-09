import os
import json
    
from langchain.chat_models import ChatOpenAI

from helper_index import JsonFlatner
from domain_corpus import DomainDataset

    
class DialogueState():

    def __init__(self, n, completion_llm, is_verbose):
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose
        gift_data = DomainDataset(dir_path="/content/drive/MyDrive/StanfordLLM/gift_qa/")
        tv_data = DomainDataset(dir_path="/content/drive/MyDrive/StanfordLLM/tv_qa/")
        ac_data = DomainDataset(dir_path="/content/drive/MyDrive/StanfordLLM/ac_qa/")
        self.raw_data = []
        for data_set in [gift_data, tv_data, ac_data]:
            for subdomain_name in data_set.subdomain_names():
                item_dict = data_set.subdomain_items(subdomain_name)
                self.raw_data.extend(item_dict.values())
        if n is not None and n < len(self.raw_data):
            self.raw_data = self.raw_data[:n]
        # self.clean_data = self.flatten_data(raw_data)

    def flatten_data(self, domain_data):
        flatner = JsonFlatner(self.completion_llm, self.is_verbose)
        for item in domain_data:  
            clean = flatner.item_summary(str(item))
            if isinstance(self.completion_llm, ChatOpenAI):
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
