import os, json
import uuid

from collections import defaultdict

# from pandas.io.json import json_normalize
from flatten_json import flatten


class JsonReader():

    def read_file(file_name, dir_path):
        try:
            print("READING=" + dir_path + file_name)
            f = open(dir_path + file_name)
            corpus_json = json.load(f)
            print("SUCCESS=" + str(file_name) + " COUNT=" + str(len(corpus_json)))
            f.close()
            return corpus_json
        except Exception as e:
            print("JSON_READER_ERROR=" + str(e))

    def list_files(dir_path):
        files = []
        for listed_item in os.listdir(dir_path):
            if "json" in listed_item:
                item_path = os.path.join(dir_path, listed_item)
                if os.path.isfile(item_path):
                    files.append(listed_item)        
        return files


class DomainDataset():

    def __init__(self, dir_path):
        file_names = JsonReader.list_files(dir_path)
        self.corpus = self.read_corpus(dir_path, file_names)

    def read_corpus(self, dir_path, file_names):
        print("\n\n" + "|| ")
        print("|| READ CORPUS")
        print("||")
        print("dir_path=" + str(dir_path) + "\t" + "file_names=" + str(file_names))

        corpus = {}
        for file_name in sorted(file_names):
            file_corpus = JsonReader.read_file(file_name, dir_path)
            corpus[file_name] = file_corpus
        return corpus
    
    def get_subdomains(self):
        return self.corpus.keys()
    
    def subdomain_corpus(self, domain_name):
        return self.corpus[domain_name]


class DatasetValidation():

    def __init__(self):
        pass
        
    def valid_corpus(any_corpus):
        return { str(k): str(v) for k, v 
                in any_corpus.items()
                if DatasetValidation.is_valid_json(v) }

    def is_valid_json(dict):
        try:
            eval(json.loads(json.dumps(str(dict))))       
            return True
        except Exception as e:
            print("INVALID_DICT=" + str(dict))
        return False


class GiftDataset(DomainDataset):

    def __init__(self, dir_path="/content/drive/MyDrive/StanfordLLM/gift_qa/"):
        super().__init__(dir_path)
    
    def get_corpus(self, domain_name):
        corpus = {}
        for item in self.subdomain_corpus(domain_name)['results']:
            corpus[str(uuid.uuid1())] = item
        return DatasetValidation.valid_corpus(corpus)     
       

class TvDataset(DomainDataset):

    def __init__(self, dir_path="/content/drive/MyDrive/StanfordLLM/tv_qa/"):
        super().__init__(dir_path)
    
    def get_corpus(self, domain_name):
        corpus = self.subdomain_corpus(domain_name)
        corpus = { k: v for k,v in corpus.items() }
        return DatasetValidation.valid_corpus(corpus)


class AcDataset(DomainDataset):

    def __init__(self, dir_path="/content/drive/MyDrive/StanfordLLM/ac_qa/"):
        super().__init__(dir_path)

    def get_corpus(self, domain_name):
        corpus = self.subdomain_corpus(domain_name)
        corpus = { k: v for k,v in corpus.items() }
        return DatasetValidation.valid_corpus(corpus)
    

# class DomainDatasets():

#     def __init__(self):
#         self.gift_data = GiftDataset(dir_path="/content/drive/MyDrive/StanfordLLM/gift_qa/")
#         self.tv_data = TvDataset(dir_path="/content/drive/MyDrive/StanfordLLM/tv_qa/")
#         self.ac_data = AcDataset(dir_path="/content/drive/MyDrive/StanfordLLM/ac_qa/")
#         self.data_sets = [self.gift_data, self.tv_data, self.ac_data]
    
    
class DomainIngestion():

    def __init__(self, data_sets, completion_llm, is_verbose):
        super().__init__()
        self.data_sets = data_sets
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose
        self.raw_data = {}
        self.domain_raw = defaultdict(list)
        self.domain_clean = defaultdict(list)
        for dataset in self.get_data_sets():
            try:
                self.ingest_dataset(dataset)
            except Exception as e:
                print("INGESTION_ERROR="+ str(e))

    def get_data_sets(self):
        return self.data_sets

    def ingest_dataset(self, dataset):
        for subdomain_name in dataset.get_subdomains():
            subdomain_corpus = dataset.get_corpus(subdomain_name)
            for key, item in subdomain_corpus.items():
                try:
                    clean = self.shorten_json(flatten(eval(item)))
                    if DatasetValidation.is_valid_json(clean):
                        self.raw_data[key] = item
                        self.domain_raw[subdomain_name].append(item)
                        self.domain_clean[subdomain_name].append(clean)
                except Exception as e:
                    print("FLATEN_ERROR=" + str(e) + " " + str(type(item)) + " " + str(item))
    
    def shorten_json(self, long):
        short = {}
        for k, v in long.items():
            key = self.shorten_key(k)
            if isinstance(v, str):
                v = v.strip()
            short[key] = v
        return short    
    
    def shorten_key(self, key):
        chain = key.split("_")
        chain = [item for item in chain if not item.isnumeric()]
        return chain[-1]    
        
    def get_raw(self):
        return self.raw_data

    def get_product(self, key):
        return self.get_raw()[key]

    def get_domain_raw(self):
        return self.domain_raw

    def get_domain_clean(self):
        return self.domain_clean