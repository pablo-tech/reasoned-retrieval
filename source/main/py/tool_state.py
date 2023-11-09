import os
import json
    
from langchain.chat_models import ChatOpenAI

from helper_index import JsonFlatner
from domain_corpus import GiftDataset, TvDataset, AcDataset

from collections import defaultdict


class DomainDatasets():

    def __init__(self):
        gift_data = GiftDataset(dir_path="/content/drive/MyDrive/StanfordLLM/gift_qa/")
        tv_data = TvDataset(dir_path="/content/drive/MyDrive/StanfordLLM/tv_qa/")
        ac_data = AcDataset(dir_path="/content/drive/MyDrive/StanfordLLM/ac_qa/")
        self.data_sets = [gift_data, tv_data, ac_data]

    def get_data_sets(self):
        return self.data_sets
    
    
class DialogueState(DomainDatasets):

    def __init__(self, n, completion_llm, is_verbose):
        super().__init__()
        self.n = n
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose
        self.raw_data = {}
        self.domain_raw = defaultdict(list)
        self.domain_clean = defaultdict(list)
        for dataset in self.get_data_sets():
            self.ingest_dataset(dataset)

    def ingest_dataset(self, dataset):
        for subdomain_name in dataset.get_subdomains():
            subdomain_corpus = dataset.get_corpus(subdomain_name)
            for key, item in subdomain_corpus.items():
                self.raw_data[key] = item
                self.domain_raw[subdomain_name].append(item)
                try:
                    flat = self.flatten_json(item)
                    self.domain_clean[subdomain_name].append(flat)
                except Exception as e:
                    print("FLATEN_ERROR=" + str(e) + " " + str(item))
                if len(self.raw_data) > self.n:
                    return

    def flatten_json(self, item):
        flatner = JsonFlatner(self.completion_llm, self.is_verbose)
        clean = flatner.item_summary(str(item))
        print("...")
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
