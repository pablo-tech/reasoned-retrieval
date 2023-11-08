import os
import json
    

class JsonReader():

    def read_corpus(dir_path, file_names):
        print("\n\n" + "|| ")
        print("|| READ CORPUS")
        print("||")
        print("dir_path=" + str(dir_path) + "\t" + "file_names=" + str(file_names))

        corpus = {}
        for file_name in sorted(file_names):
            file_corpus = JsonReader.read_file(file_name, dir_path)
            corpus.update(file_corpus)
        return corpus

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


class GiftSummary():
    
    def summary_instruction():
        return """
You are an AI that summarizes complex JSON objects.
"""


class GiftDataset():

    def __init__(self, dir_path="/content/drive/MyDrive/TataLLM/GiftReader/"):
        file_names = JsonReader.list_files(dir_path)
        files_data = [JsonReader.read_file(file_name, dir_path) for file_name in file_names]
        self.raw_data = []
        for file_data in files_data:
            for item in file_data:
              self.raw_data.append(item)
                


class GiftRetriever():

    def __init__(self, completion_llm, is_verbose):
        super().__init__(completion_llm, is_verbose)
        self.doc_store = {}

    def subquery(self, query):
        pass
