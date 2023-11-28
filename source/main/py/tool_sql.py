from helper_suql import ContextParser, InferenceParser, WholisticParser
from domain_knowledge import GiftDataset2, TvDataset, AcDataset

from model_base import OpenaiBase

import sqlite3


class DatabaseInstance():
    
    def __init__(self, 
                 database_name="tutorial.db"):
        self.db_connection = sqlite3.connect(database_name)
        self.db_cursor = self.db_connection.cursor()

    def get_db_connection(self):
        return self.db_connection

    def get_db_cursor(self):
        return self.db_cursor


class GiftOracle():

    def __init__(self, is_run_inference, subdomain_names, completion_llm):
        domain_name="CLIQ"
        picked_columns=['id', 'price', 
                        'brand', 'colors', 'gender',
                        'title', 'description', 'sub_domain'] # 'category', 'store', 
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
        self.inference_parser = InferenceParser(is_run_inference, domain_name, self.subdomain_dataset_func, 
                                                subdomain_names, subdomain_column,
                                                picked_columns, primary_key, price_column,  
                                                summarize_columns, column_annotation, 
                                                self.db_instance, completion_llm, is_verbose=False)
        self.wholistic_parser = WholisticParser(self.context_parser, self.inference_parser)

    def subdomain_dataset_func(self, subdomain_names):
        return [GiftDataset2(subdomain_names)]
    
    def get_context_parser(self):
        return self.context_parser

    def get_inference_parser(self):
        return self.inference_parser

    def get_wholistic_parser(self):
        return self.wholistic_parser

    def get_db_cursor(self):
        return self.db_instance.get_db_cursor()

    def get_annotation(self):
        return { 
            "for_people": {
                "style_setters": ["dinner_sets", "candle_holders", "candles"], 
                "wellness_lovers": ["dryfruits", "tea_sets"], 
                "fitness_buffs": ["speaker_mediaplayer"], 
                "gamers": ["gaming", "headphones_earphones"], 
                "home_chefs": ["dinner_sets"], 
                "gear_heads": [], 
                "DIYers": [],
                "adventure_seekers": [], 
                "trending_gifts": []
                },
            "shop_gifts": {
                "for_her": ["wallets-women", "watch-women", "fragrances-women", "handbags-women", "backpacks-women", "clutches-women"], 
                "for_him": ["wallets-men", "watch-men", "fragrances-men", "backpacks-men"], 
                "for_teens": [], 
                "for_kids": ["watch-kids", "watch-kids"],
                "babies_and_toddlers": [], 
                "for_pets": [],
                "for_retirement": ["watch-men", "watch-women"],
                "for_mom": ["watch-women", "fragrances-women", "handbags-women"],
            },
            "by_category": {
                "electronics": ["headphones_earphones", "instant_camera", "mobiles", "speaker_mediaplayer", "tab_ereader"], 
                "fashion": [], 
                "home_and_kitchen": ["bedsheets", "candle_holders", "dinner_sets", "tea_sets", "home_fragrances"],
                "sports_and_outdoors": [], 
                "jewelry": ["silver_artifacts", "clutches"],
                "beauty": []
                },
            "holiday_shopping": {
                "most_loved_gifts": ["chocolates", "sweets"], 
                "decor": ["candle_holders", "silver_artifacts"],
                "valentines": ["chocolates"],
                "gifts_for_all": ["drinking_glass"], 
                "toys": [], 
                "stocking_stuffers": ["chocolates", "sweets"],
                "unique_gifts": ["silver_bullion"], 
                "hosting_essentials": [], 
                "white_elephant": [],
                "same_day_delivery": []
            }
        } 

class ProductRetriever():

    def __init__(self):
        pass


class ProductReader():

    def __init__(self):
        pass    