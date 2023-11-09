import os
import json
    
from langchain.chat_models import ChatOpenAI

from helper_index import JsonFlatner
from domain_corpus import GiftDataset, TvDataset, AcDataset

from collections import defaultdict

    
class DialogueState():

    def __init__(self, n, completion_llm, is_verbose):
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose
        gift_data = GiftDataset(dir_path="/content/drive/MyDrive/StanfordLLM/gift_qa/")
        tv_data = TvDataset(dir_path="/content/drive/MyDrive/StanfordLLM/tv_qa/")
        ac_data = AcDataset(dir_path="/content/drive/MyDrive/StanfordLLM/ac_qa/")
        self.raw_data = {}
        self.domain_raw = defaultdict(list)
        self.domain_clean = defaultdict(list)
        for dataset in [gift_data, tv_data, ac_data]:
            for name in dataset.get_subdomains():
                i = 0
                corpus = dataset.get_corpus(name)
                for key, item in corpus.items():
                    self.raw_data[key] = item
                    if i < n:
                        self.domain_raw[name].append(item)
                        flat = self.flatten_json(item)
                        self.domain_clean[name].append(flat)
                        i += 1

    def flatten_json(self, item):
        flatner = JsonFlatner(self.completion_llm, self.is_verbose)
        clean = flatner.item_summary(str(item))
        if isinstance(self.completion_llm, ChatOpenAI):
            clean = clean.content
        return json.loads(clean)
    
    def get_raw(self):
        return self.raw_data

    def get_product(self, key):
        return self.get_raw()[key]

    def get_domain_raw(self):
        return self.domain_raw

    def get_domain_clean(self):
        return self.domain_clean
    
    # def get_store(self):
    #     return { item['title']: item for item in self.get_clean()}
    


class GiftRetriever():

    def __init__(self, completion_llm, is_verbose):
        super().__init__(completion_llm, is_verbose)
        self.doc_store = {}

    def subquery(self, query):
        pass
