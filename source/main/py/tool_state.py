import os
import json
    

    
    # def get_store(self):
    #     return { item['title']: item for item in self.get_clean()}

class DialogState():

    def __init__(self):
        pass    
    

class GiftRetriever():

    def __init__(self, completion_llm, is_verbose):
        super().__init__(completion_llm, is_verbose)
        self.doc_store = {}

    def subquery(self, query):
        pass
