from helper_suql import ContextParser, InferenceParser
from helper_parser import SemanticQuery
from domain_knowledge import GiftDataset2, TvDataset, AcDataset

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
        db_connection().commit()
        db_connection.close()

    def execute_read(self, query):
        db_connection = self.new_connection()
        db_cursor = db_connection.cursor()
        db_cursor.execute(query)
        response = db_cursor.fetchall()
        db_connection.close()
        return response 

class GiftOracle():

    def __init__(self, is_run_inference, subdomain_names, completion_llm):
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
        return [GiftDataset2(subdomain_names)]
    
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


class QueryFactory():

    def __init__(self, query_limit, domain_oracle, completion_llm, db_instance):
        self.domain_oracle = domain_oracle
        self.inference_queries = {}
        sub_domains = self.domain_oracle.get_context_parser().get_subdomain_names()
        inference_parser = domain_oracle.get_inference_parser()
        for sub_domain in sub_domains:
            inference_query = SemanticQuery(
                query_limit=query_limit,
                invocations=inference_parser.get_invocations(sub_domain),
                completion_llm=completion_llm,
                db_instance=db_instance)
            self.inference_queries[sub_domain] = inference_query

    def executable_names(self):
        return list(self.inference_queries.keys())

    def new_model(self, executable_name):
        return self.inference_queries[executable_name]
    

class ProductRetriever():

    def __init__(self):
        pass


class ProductReader():

    def __init__(self):
        pass    