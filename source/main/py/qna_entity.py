# from qna_spacy import SpacyProcessor


# class BrandRecognition():

#     def __init__(self):
#         self.tv_brands = ["Samsung", "LG", "Sony", "Croma", "TCL", "Hisense", "SANSUI",
#                           "Akai", "Haier", "Kodak", "One Plus", "Acer", "Foxsky", "Panasonic",
#                           "Philips", "SAMSUNG", "Realme", "Aiwa", "Treeview", "Xiaomi",
#                           "Kevin", "Kindle", "Toshiba", "Apple", "HYUNDAI", "Redmi",
#                           "Fingers", "Karbonn", "Candy", "Detel", "PGold", "Electron",
#                           "IFFALCON", "Airtel", "Bandridge", "Foxsky", "OnePlus",
#                           "Portronics", "Sensy", "Sun King", "TCL", "UltraProlink", "Android",
#                           "Tizen", "WebOS", "Linux", "Fire", "Bravia",
#                           "QLED", "OLED", "LED"] 
#         self.ac_brands = ["Voltas", "Blue Star", "O General", "Panasonic", "Daikin", "Hitachi",
#                           "Samsung", "Croma", "Haier", "LG", "Lloyd", "Mitsubishi", "Electrolux",
#                           "Whirlpool", "Hisense", "IFB", "Carrier", "Candy", "Godrej", "Lloyd", 
#                           "Midea", "Whirlpool"] 
#         self.brands = set(self.tv_brands).union(set(self.ac_brands))
#         self.brands = { w.lower() for w in self.brands }
#         # LogMessage.write("BRANDS ------> " + str(self.brands))

#     def all_brands(self):
#         brands = ""
#         for brand in sorted(self.brands):
#             brands += brand + ", "
#         return brands
    
#     def brand_entities(self, texts):
#         text = " ".join(texts)
#         words = { str(w.lower()) for w in text.split((" ")) } 
#         # LogMessage.write("WORDS ------> " + str(words))
#         entities = { w for w in words if w in self.brands }
#         return entities


class EntityRecognition():

    def __init__(self):
        self.text_processor = SpacyProcessor()

    def org_entities(self, texts):
        entities = self.text_processor.label_entities(texts, 'ORG')            
        return { str(e) for e in entities }