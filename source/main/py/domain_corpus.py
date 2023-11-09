import os, json
import uuid


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
    

class GiftDataset(DomainDataset):

    def __init__(self, dir_path):
        super().__init__(dir_path)
    
    def get_corpus(self, domain_name):
        corpus = {}
        for item in self.subdomain_corpus(domain_name)['results']:
            corpus[uuid.uuid1()] = item
        return corpus


class TvDataset(DomainDataset):

    def __init__(self, dir_path):
        super().__init__(dir_path)
    
    def get_corpus(self, domain_name):
        return self.subdomain_corpus(domain_name)


class AcDataset(DomainDataset):

    def __init__(self, dir_path):
        super().__init__(dir_path)

    def get_corpus(self, domain_name):
        return self.subdomain_corpus(domain_name)


