from langchain.agents import Tool

from vector_db import PineconeDb

from helper_select import SelectHelper


class VectorRetriever(SelectHelper):
    # https://pypi.org/project/wikipedia/

    def __init__(self, 
                 completion_llm, 
                 is_verbose=False):
        super().__init__("PINECONE", completion_llm, is_verbose)
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose
        self.doc_store = PineconeDb(index_name="quickstart",
                                    is_create=True)
        self.load_faq()
        self.load_docs()
        print(self.doc_store.__str__())

    def load_faq(self,
                 files=['joined_faq.csv'], 
                 path='/content/drive/MyDrive/StanfordLLM/qa_data/faq_qa/',):
        docs = self.doc_store.read_files(file_names=files,
                                             directory_path=path)
        begins = [" ".join(doc.page_content.split(" ")[:3]).lstrip('\"') 
                for doc in docs]
        metas = [{'begins':str(begin)} for begin in begins]        
        self.doc_store.load_docs(items=docs, metas=metas)        
        
    def load_docs(self,
                  files=['pay-user.txt',
                        'payoff-sale.txt',
                        'refer-and-earn.txt',
                        'sale-parade.txt',
                        'savings-calculator.txt',
                        'seller-terms.txt',
                        'tdl-privacy.txt',
                        'terms-conditions.txt',
                        'tpl-privacy.txt'],
                   path='/content/drive/MyDrive/StanfordLLM/qa_data/legal_qa/'):
        docs = self.doc_store.read_files(files, path)        
        metas = []
        self.doc_store.load_docs(items=docs, metas=metas)  


class VectorSearchReader(VectorRetriever):

    def __init__(self, completion_llm, is_verbose=False):
        super().__init__(completion_llm, is_verbose)

    def run(self, tool_input, user_query=""):
        return self.invoke(tool_input, self.select)

    def select(self, query):
        results = self.subquery(query)
        return self.answer(self.summarize(results, query), query)

    def subquery(self, query, k=5, n=5):
        results = []
        try:
          results = self.doc_store.search(query, k)
          results = results['matches']
        #   results = [str(r['text']).strip() for r in results]
        except Exception as e:
          # print("SEARCH_SUBQUERY_ERROR=" + str(e))
          return [str(e)]
        print("RESULTS="+str(results))
        return results
        # snippets = []
        # for result in results:
        #   try:
        #     snippets.append(self.doc_store.summary(result,
        #                                            sentences=n))
        #   except Exception as e:
        #     # print("SEARCH_SUMMARIZE_ERROR=" + str(e))
        #     pass
        #   if len(snippets) >= k:
        #     return snippets
        # return snippets


class VectorToolFactory():

    def __init__(self, completion_llm, is_verbose=False):
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose

    def get_tools(self):
        search = VectorSearchReader(self.completion_llm, self.is_verbose)

        return [
          Tool(
              name="Search",
              func=search.run,
              description="useful to search for the truth"
          )
        ]
