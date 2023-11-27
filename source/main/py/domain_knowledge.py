import os, json
import uuid
import json 

from collections import defaultdict

from flatten_json import flatten


class JsonReader():

    def read_file(file_name, dir_path, is_verbose=False):
        try:
                # print("READING=" + dir_path + file_name)
            f = open(dir_path + file_name)
            corpus_json = json.load(f)
            if is_verbose:
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

    def __init__(self, subdomain_names, dir_path, is_verbose=False):
        self.is_verbose = is_verbose
        if len(subdomain_names) == 0:
            file_names = JsonReader.list_files(dir_path)
        else:
            file_names = subdomain_names
        self.corpus = self.read_corpus(dir_path, file_names)

    def read_corpus(self, dir_path, file_names):
        if self.is_verbose:
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


class CromaDataset(DomainDataset):

    def __init__(self, subdomain_names, dir_path):
        super().__init__(subdomain_names, dir_path=dir_path)

    def get_corpus(self, domain_name):
        corpus = self.subdomain_corpus(domain_name)
        corpus = { v['id']: self.clean_body(v) for k,v in corpus.items() }
        return DatasetValidation.valid_corpus(corpus)

    def clean_body(self, product):
        replica = product.copy()
        cleansed = ''
        for section in product['body'].copy():
            for feature in section:
                if isinstance(feature, list):
                    for bullet in feature:
                        # print(bullet)
                        if isinstance(bullet, list):
                            if len(cleansed) != 0:
                                cleansed += "\n"  
                            cleansed += bullet[0] 
                            if cleansed[-1] not in [".", "!", "?"]:
                                cleansed += "."
        replica['body'] = cleansed
        return replica          


class TvDataset(CromaDataset):

    def __init__(self, dir_path="/content/drive/MyDrive/StanfordLLM/qa_data/tv_qa/"):
        super().__init__(subdomain_names=[], dir_path=dir_path)
    

class AcDataset(CromaDataset):

    def __init__(self, dir_path="/content/drive/MyDrive/StanfordLLM/qa_data/ac_qa/"):
        super().__init__(subdomain_names=[], dir_path=dir_path)


class GiftDataset(DomainDataset):

    def __init__(self, dir_path="/content/drive/MyDrive/StanfordLLM/qa_data/gift_qa/"):
        super().__init__(subdomain_names=[], dir_path=dir_path)
    
    def get_corpus(self, domain_name):
        corpus = {}
        for product in self.subdomain_corpus(domain_name)['results']:
            corpus[str(uuid.uuid1())] = product
        return DatasetValidation.valid_corpus(corpus)     


class GiftDataset2(DomainDataset):

    def __init__(self, subdomain_names,
                 dir_path="/content/drive/MyDrive/StanfordLLM/qa_data/gift2_qa/"):
        super().__init__(subdomain_names, dir_path)
    
    def get_corpus(self, domain_name):
        corpus = {}
        for product in self.subdomain_corpus(domain_name): # ['results']
            corpus[str(uuid.uuid1())] = product
        return DatasetValidation.valid_corpus(corpus)


class GiftSuql():

    def __init__(self, 
                 dir_path="/content/drive/MyDrive/StanfordLLM/qa_data/suql_qa/"):
        self.dir_path = dir_path

    def file_path(self, sub_domain):
        return self.dir_path + sub_domain

    def save_corpus(self, sub_domain, products):
        file_path = self.file_path()
        print("saving... " + str(file_path))
        try:
            os.remove(file_path)
        except:
            pass
        try:
            with open(file_path, 'w') as fp:
                json.dump(products, fp)        
        except:
            print("SAVE_FILE_ERROR="+str(sub_domain))
            pass

    def get_corpus(self, domain):
        print("reading... " + str(domain))
        file_path = self.file_path(domain)
        products = []
        try:
            with open(file_path, 'r') as fp:
                products = json.load(fp)        
        except:
            print("READ_FILE_ERROR="+str(domain))
            pass
        return products


class DomainIngestion():

    def __init__(self, data_sets, 
                 subdomain_name, subdomain_column,
                 completion_llm, is_verbose):
        self.data_sets = data_sets
        self.subdomain_name = subdomain_name
        self.subdomain_column = subdomain_column
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose
        self.raw_data = {}
        self.clean_data = {}
        self.domain_clean = defaultdict(dict)
        for dataset in self.get_data_sets():
            try:
                self.ingest_dataset(dataset)
            except Exception as e:
                print("INGESTION_ERROR="+ str(e))

    def get_data_sets(self):
        return self.data_sets

    def ingest_dataset(self, dataset):
        n = 0
        for subdomain_name in dataset.get_subdomains():
            subdomain_corpus = dataset.get_corpus(subdomain_name)
            n += len(subdomain_corpus)
            print(subdomain_name+"="+str(len(subdomain_corpus)))
            for key, raw_product in subdomain_corpus.items():
                try:
                    raw_product = eval(raw_product)
                    clean_product = self.shorten_json(flatten(raw_product))
                    clean_product = self.legal_product(clean_product)
                    clean_product[self.subdomain_column] = subdomain_name
                    if DatasetValidation.is_valid_json(clean_product):
                        self.raw_data[key] = raw_product
                        self.clean_data[key] = clean_product
                        self.domain_clean[subdomain_name][key] = clean_product
                except Exception as e:
                    print("FLATEN_ERROR=" + str(e) + " " + str(type(raw_product)) + " " + str(raw_product))
        print("DATASET_SIZE="+str(n))

    def legal_product(self, product_in):
        product_out = {}
        for k, v in product_in.items():
            k = self.legal_key(k)
            product_out[k] = v
        return product_out

    def legal_key(self, key):
        key = key.replace("/", "")
        key = key.replace("__", "_")
        key = key.replace("__", "_") 
        key = key.replace("%", "percent") 
        return key           
    
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
        
    def get_raw_products(self):
        return self.raw_data
    
    def get_all_products(self):
        return list(self.clean_data.values())
    
    def get_domain_products(self):
        products = self.get_all_products() 
        if self.subdomain_name == "":
            return products
        return [p for p in products 
                if p[self.subdomain_column]==self.subdomain_name]

    def get_product(self, key):
        return self.clean_data[key]

    def get_subdomain_products(self):
        return self.domain_clean
    
    def get_subdomain_names(self):
        subdomain_products = self.get_all_products()
        return sorted(list(set([p[self.subdomain_column] 
                                for p in subdomain_products])))


class DomainSchema(DomainIngestion):

    def __init__(self, data_sets, 
                 subdomain_name, subdomain_column,
                 completion_llm, is_verbose):
        super().__init__(data_sets, 
                         subdomain_name, subdomain_column,
                         completion_llm, is_verbose)
        self.slot_values = defaultdict(set)

    def get_domain_columns(self):
        all_columns = set()
        for subdomain_data in self.get_subdomain_products().values():
            for item in subdomain_data.values():
                item_columns = list(item.keys())
                item_columns = [ self.normal_name(column) for column in item_columns ]
                all_columns.update(item_columns)
        column_names = { self.normal_name(column) for column in all_columns}
        return sorted(list(column_names))

    def normal_name(self, text):
        text = text.replace(" ", "_")
        text = text.replace("/", "_")
        text = text.replace("&", "_")
        text = text.replace(".", "_")
        text = text.replace("(", "")
        text = text.replace(")", "")
        return text.lower()
        