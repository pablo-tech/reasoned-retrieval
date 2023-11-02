import os

from langchain.utilities import SerpAPIWrapper
from serpapi import GoogleSearch


class SearchEngine(SerpAPIWrapper):
# https://github.com/langchain-ai/langchain/blob/master/libs/langchain/langchain/utilities/serpapi.py
    
    def __init__(self):
        # https://serpapi.com/dashboard
        super().__init__(serpapi_api_key = '2c24c5acccd4ab1f8644348773293cac5aa6907314eb0685ab2d8ad3d75e528d')
        # self.serpapi_api_key = '2c24c5acccd4ab1f8644348773293cac5aa6907314eb0685ab2d8ad3d75e528d'
        # os.environ["SERPAPI_API_KEY"] = self.serpapi_api_key

    def configurable_results(self, query):
        params = self.configurable_params(query)
        engine = GoogleSearch(params)
        results = engine.get_dict()
        # results = self.results(query)
        return results 

    def configurable_params(self, query, k=15):
        # https://serpapi.com/search-api
        return {'api_key': self.serpapi_api_key,
                'q': query,
                'num': k,                 
                'engine': 'google', 
                'google_domain': 'google.com', 
                'hl': 'en', 
                'gl': 'us', 
                'device': 'desktop'}
    

class SearchAnswer(SearchEngine):

    def __init__(self):
        super().__init__()

    def run(self, query):
        return self.summarize(self.organic(self.select(query)))

    def summarize(self, results):
        return [result['snippet'] for result in results]

    def organic(self, results):
        try:
          organic = results["organic_results"]
          # print(results["search_information"])
          # print(str(organic))
          # print(str(results.keys()))
          return organic
        except:
          print(str(results['error']))
          print(str(results))

    def info(self, query):
        return self.select(query)["search_information"]

    def pagination(self, query):
        return self.select(query)['serpapi_pagination']

    def select(self, query):
        return self.configurable_results(query)
    

