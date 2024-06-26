from langchain.agents import Tool

from helper_suql import ContextParser, InferenceParser
from helper_parser import SemanticQuery, QueryFactory
from domain_knowledge import GiftDataset2, TvDataset, AcDataset
from model_executor import PayloadFactory, QueryExecutor, ModelExecutor
from helper_select import SelectHelper
from model_base import OpenaiBase

import sqlite3


class DatabaseInstance():
    
    def __init__(self, 
                 database_name="tutorial.db"):
        self.database_name = database_name

    def new_connection(self):
        return sqlite3.connect(self.database_name,
                               check_same_thread=False,
                               timeout=20)        

    def execute_create(self, query):
        db_connection = self.new_connection()
        db_cursor = db_connection.cursor()
        db_cursor.execute(query)
        db_connection.close()

    def execute_write(self, query):
        db_connection = self.new_connection()
        db_cursor = db_connection.cursor()
        db_cursor.execute(query)
        db_connection.commit()
        db_connection.close()

    def execute_read(self, query):
        db_connection = self.new_connection()
        db_cursor = db_connection.cursor()
        db_cursor.execute(query)
        response = db_cursor.fetchall()
        db_connection.close()
        return response 

class GiftOracle():

    def __init__(self, is_run_inference, 
                 subdomain_names, completion_llm,
                 dataset_path):
        self.dataset_path = dataset_path
        domain_name="CLIQ"
        picked_columns=['id', 'price', 
                        'brand', 'colors', 'gender',
                        'title', 'description'] 
        primary_key='id'
        price_column = 'price'
        summarize_columns=['title', 'description']
        subdomain_column = 'sub_domain'
        self.db_instance = DatabaseInstance()
        self.context_parser = ContextParser(domain_name, self.subdomain_dataset_func, 
                                            subdomain_column,
                                            picked_columns, primary_key, price_column, summarize_columns,
                                            self.db_instance, completion_llm, is_verbose=False)
        column_annotation = self.get_annotation()  
        if len(subdomain_names) == 0:
            subdomain_names = self.context_parser.get_subdomain_names()    
        self.inference_parser = InferenceParser(self.context_parser, is_run_inference, domain_name, self.subdomain_dataset_func, 
                                                subdomain_names, subdomain_column,
                                                picked_columns, primary_key, price_column,  
                                                summarize_columns, column_annotation, 
                                                self.db_instance, completion_llm, is_verbose=False)

    def subdomain_dataset_func(self, subdomain_names):
        return [GiftDataset2(subdomain_names=subdomain_names,
                             dir_path=self.dataset_path)]
    
    def get_context_parser(self):
        return self.context_parser

    def get_inference_parser(self):
        return self.inference_parser

    def get_db_instance(self):
        return self.db_instance    

    def get_annotation(self):
        return { 
            "for_people": {
                "style_setters": ["dinner_sets", "candle_holders", "candles"], 
                "wellness_lovers": ["dryfruits", "tea_sets"], 
                "fitness_buffs": ["speaker_mediaplayer"], 
                "gamers": ["gaming", "headphones_earphones"], 
                "home_chefs": ["dinner_sets"], 
                # "gear_heads": [], 
                # "DIYers": [],
                # "adventure_seekers": [], 
                # "trending_gifts": []
                },
            "shop_gifts": {
                "for_mom": ["wallets-women", "handbags-women", "backpacks-women"], 
                "for_her": ["watch-women", "fragrances-women",  "clutches-women"], 
                "for_him": ["watch-men", "fragrances-men"], 
                "for_dad": ["wallets-men","backpacks-men"], 
                "for_kids": ["watch-kids", "watch-kids"],
                "for_retirement": ["watch-men", "watch-women"],
                # "for_teens": [], 
                # "babies_and_toddlers": [], 
                # "for_pets": [],
            },
            "by_category": {
                "electronics": ["headphones_earphones", "instant_camera", "mobiles", "speaker_mediaplayer", "tab_ereader"], 
                "home_and_kitchen": ["bedsheets", "candle_holders", "dinner_sets", "tea_sets", "home_fragrances"],
                "sports_and_outdoors": [], 
                "jewelry": ["silver_artifacts", "clutches"],
                # "beauty": []
                # "fashion": [], 
                },
            "holiday_shopping": {
                "most_loved_gifts": ["chocolates", "sweets"], 
                "valentines_day": ["chocolates"],
                "decor": ["candle_holders", "silver_artifacts"],
                "gifts_for_all": ["drinking_glass"], 
                "stocking_stuffers": ["chocolates", "sweets"],
                "unique_gifts": ["silver_bullion"], 
                # "toys": [], 
                # "hosting_essentials": [], 
                # "white_elephant": [],
                # "same_day_delivery": []
            }
        } 
    

class ProductRetriever(SelectHelper):

    def __init__(self, discretize_llm, parsing_llm, is_verbose, dataset_path):
        super().__init__("CLIQ", discretize_llm, is_verbose)
        domain_oracle = GiftOracle(is_run_inference=False,
                                   subdomain_names=[],
                                   completion_llm=discretize_llm,
                                   dataset_path=dataset_path)
        ### CONTEXT
        print(domain_oracle.get_context_parser().default_columns())
        print(domain_oracle.get_context_parser().get_columns())
        print(domain_oracle.get_context_parser().get_schema_sql())
        print(domain_oracle.get_context_parser().get_products()[0])
        coluns, rows = domain_oracle.get_context_parser().load_items()
        print(domain_oracle.get_context_parser().get_enum_values())
        print(domain_oracle.get_context_parser().get_fewshot_examples())
        print(domain_oracle.get_context_parser().get_subdomain_names())
        ### INFERENCE
        print(len(domain_oracle.get_inference_parser().get_columns('backpacks-men.json')))
        print(domain_oracle.get_inference_parser().join_schema_sql("backpacks-men.json"))
        domain_oracle.get_inference_parser().load_items()
        print(domain_oracle.get_inference_parser().join_enum_values("backpacks-men.json"))
        ### SQL: see more at SQLTool-ProductSearch
        # for r in domain_oracle.get_db_instance().execute_read("""
        # SELECT COUNT(*) FROM 'CLIQ_INFERENCE_FRAGRANCES_WOMEN_JSON';"""):
        # print(r[0])
        ### EXECUTOR
        # products = domain_oracle.get_inference_parser().get_products('fragrances-men.json')
        self.query_executor = QueryExecutor()
        # model_executor = ModelExecutor()
        self.query_factory = QueryFactory(query_limit=1, 
                                          domain_oracle=domain_oracle, 
                                          completion_llm=parsing_llm)

    def subquery(self, query_txt, query_filter):
        try:
            query_models = [self.query_factory.get_model(sub_domain)
                            for sub_domain in query_filter.values()]            
            payloads = PayloadFactory(query_txt, query_models).get_payloads()
            return self.query_executor.execute_queries(payloads)
        except Exception as e:
            error = "SLIQ_SUBQUERY_ERROR="+str(e)+"...WITH_QUERY="+str(query_txt)+"...QUERY_FILTER="+str(query_filter)
            print(error)
            return [error]


class ProductsReader(ProductRetriever):

    def __init__(self, discretize_llm, parsing_llm, is_verbose, dataset_path):
        super().__init__(discretize_llm, parsing_llm, is_verbose, dataset_path)

    def run(self, tool_input, user_query, query_filter): 
        # TODO: query_filter = domain_oracle.get_context_parser().get_subdomain_names()]).get_payloads()
        return self.invoke(tool_input, query_filter, self.select)

    def select(self, query_txt, query_filter):
        results = self.subquery(query_txt, query_filter)
        return self.answer(self.summarize(results, query_txt), query_txt)


class SqlToolFactory():

    def __init__(self, discretize_llm, parsing_llm, is_verbose=False,
                 dataset_path="/content/drive/MyDrive/StanfordLLM/qa_data/gift2_qa/"):
        self.discretize_llm = discretize_llm
        self.parsing_llm = parsing_llm
        self.is_verbose = is_verbose
        self.dataset_path = dataset_path

    def get_tools(self):
        api = ProductsReader(self.discretize_llm, self.parsing_llm, 
                            self.is_verbose, self.dataset_path)
        return [
          Tool(
              name="ProductSearch",
              func=api.run,
              description="useful access to a database of products"
          )
        ]    