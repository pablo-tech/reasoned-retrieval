from langchain.document_loaders import TextLoader
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.document_loaders import JSONLoader
from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter

from vector_embed import BytePairEmbedding

import pinecone
from langchain.vectorstores import Pinecone

from uuid import uuid4
    

class VectorDb():

    def __init__(self,
                chunk_size=1000,
                chunk_overlap=100):
        self.embedding_model = BytePairEmbedding
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size = chunk_size,
                                                            chunk_overlap  = chunk_overlap,
                                                            length_function = len,
                                                            separators = ["\n\n", "\n", " ", ""],
                                                            is_separator_regex = False)
        self.embed_dimension = len(self.get_vector("x"))

    def read_files(self, file_names,
                  directory_path='/content/drive/MyDrive/StanfordLLM/qa_data/legal_qa/'):
        file_names = [directory_path+name for name in file_names]      
        return self.text_documents(file_names)

    def read_faq(self, file_names):
        return self.csv_documents(file_names)
    
    def read_products(self, 
                      file_names,
                      directory_path='/content/drive/MyDrive/StanfordLLM/qa_data/faq_qa/'):
        file_names = [directory_path+name for name in file_names]            
        return self.json_documents(file_names)

    def text_documents(self, file_names):
        split_documents = []
        for file_name in file_names:
          whole_document = TextLoader(file_name).load()
          split_documents += self.text_splitter.split_documents(whole_document)    
        return split_documents

    def csv_documents(self, file_names):
        split_documents = []
        for file_name in file_names:
          whole_document = CSVLoader(file_name).load()
          split_documents += self.text_splitter.split_documents(whole_document)    
        return split_documents
        
    def product_metadata_func(self, record: dict, metadata: dict) -> dict:
        # price is meta but not categorical
        metadata["brand"] = record.get("brand")
        metadata["store"] = record.get("store")
        metadata["gender"] = record.get("gender")
        metadata["category"] = record.get("category")
        metadata["product_id"] = record.get("product_id")
        metadata["price"] = record.get("price")
        return metadata
            
    def json_documents(self, file_names):
        # https://python.langchain.com/docs/modules/data_connection/document_loaders/json
        split_documents = []
        for file_name in file_names:
          loader = JSONLoader(
                file_path=file_name,
                jq_schema=".[]", # ".[].description", # ".[]", # 
                content_key="description",
                metadata_func=self.product_metadata_func)
          whole_documents = loader.load()
          split_documents += whole_documents
          # split_documents += self.text_splitter.split_documents(whole_document)    
        return split_documents

    def get_vector(self, text):
        return self.embedding_model.embed_query(text)

    def calc_embeds(self, texts):
        return [self.get_list_vector(text) for text in texts]

    def get_list_vector(self, text):
        return self.get_vector(text).tolist()

    def new_ids(self, items):
        return [str(uuid4()) for _ in range(len(items))]


class PineconeEnv(VectorDb):

    def __init__(self,
                api_key="9be7c0e1-612e-43f4-ae72-b572832f3131",
                environment="gcp-starter"):
        super().__init__()
        self.api_key = api_key
        self.environment = environment


class PineconeCore(PineconeEnv):
    
    def __init__(self,
                 index_name,
                 is_create,
                 similarity_metric='cosine', # "euclidean"
                 shard_count=1):
        super().__init__()   
        self.index_name = index_name
        self.is_create = is_create
        self.similarity_metric = similarity_metric
        self.shard_count = shard_count
        self.db_init()
        self.db_index = pinecone.Index(self.index_name,
                                       pool_threads=1)

    def db_init(self):
        pinecone.init(api_key=self.api_key, environment=self.environment)
        if self.is_create:
          try:
            pinecone.delete_index(self.index_name)
            # index = pinecone.GRPCIndex(index_name)
          except:
            pass
          pinecone.create_index(self.index_name, 
                                dimension=self.embed_dimension, 
                                metric=self.similarity_metric,
                                shards=self.shard_count) 

    def get_index(self):
        return self.db_index

    def __str__(self):
        return f"""
  {pinecone.list_indexes()}
  {self.get_index().describe_index_stats()}
  """


class PineconeIO(PineconeCore):

    def __init__(self, 
                 index_name, 
                 is_create):
        super().__init__(index_name, is_create)
        self.CHUNK_COL = "chunk"
        self.TEXT_COL = "text"
        
    def join_upsert(self, ids, embeds, metadatas):
        insertable = zip(ids, embeds, metadatas)
        # print("000" + str(list(insertable)[0][2]))
        self.get_index().upsert(vectors=insertable,
                                async_req=False)

    def batch_upsert(self, items, metadatas,
                     upsert_func, batch_size=100):
        i = 0
        while i < len(items):
          j = i+batch_size
          if j > len(items):
            j = len(items)
          upsert_func(items[i:j], metadatas[i:j])
          i+=batch_size

    def search(self, search_txt, k, search_filter={}):
        return self.select_by_text(search_txt, k, search_filter)

    def select_by_text(self, 
                       search_txt, 
                       k,
                       search_filter,
                       include_metadata=True,
                       include_vectors=False):
        return self.select_by_vector(search_vec=self.get_list_vector(search_txt),
                                     k=k,
                                     search_filter=search_filter,
                                     include_metadata=include_metadata,
                                     include_vectors=include_vectors)

    def select_by_vector(self, 
                         search_vec,
                         k,                        
                         search_filter,
                         include_metadata,
                         include_vectors):
        print("search_filter="+str(search_filter))
        results_with_scores = self.get_index().query(vector=search_vec,
                                                     top_k=k,
                                                     filter=search_filter,
                                                     include_metadata=include_metadata,
                                                     include_values=include_vectors)
        return results_with_scores    
    
    def fetch_by_id(self, ids):
        return self.get_index().fetch(ids)
    
    def delete_by_id(self, ids):
        return self.get_index().delete(ids)



class PineconeDb(PineconeIO):

    def __init__(self, index_name, is_create=False):
        super().__init__(index_name,
                         is_create)
    
    def load_docs(self, items, metas):
        if len(metas) == 0:
            metas=[{} for _ in range(len(items))]
        self.batch_upsert(items, metas, 
                          upsert_func=self.doc_upsert)

    def doc_upsert(self, docs, metadatas):
        ids = self.new_ids(docs)
        embeds = self.calc_embeds([doc.page_content for doc in docs])
        metadatas = self.docs_metadata(docs, metadatas)
        self.join_upsert(ids, embeds, metadatas)

    def docs_metadata(self, docs, metadatas):
        return [self.doc_metadata(docs[i], metadatas[i], i)
                for i in range(len(docs))]

    def doc_metadata(self, doc, metadata, chunk):
        return { self.CHUNK_COL: chunk, 
                 self.TEXT_COL: doc.page_content, 
                 **doc.metadata,
                 **metadata } 