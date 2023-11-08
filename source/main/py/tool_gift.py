# from qna_reader import JsonReader
# from qna_log import LogMessage
# from qna_example import ContentExample
# from qna_croma_text import CromaText
# from qna_tag import TagProcessor
# from qna_tag import TagCorpus

import os
import json
import uuid

# from qna_log import LogMessage
# from qna_example import ContentExample


from collections import namedtuple

# from qna_log import LogMessage
# from qna_tuple import ContentSection, SectionElement


ContentSection = namedtuple('ContentSection', ['heading', 'elements', 'knowledge', 'id'])
SectionElement = namedtuple('SectionElement', ['text', 'knowledge', 'id'])


class ContentExample():

  KNOWLEDGE_KEY = "knowledge"
  BODY_KEY = "body"
  SPECIFICATION_KEY = "specification"
  URL_KEY = "url"
  PRICE_KEY = "price"
  PRODUCT_CODE = "code"
  PRODUCT_IMAGES = "images"


  def __init__(self, domain, source, title, subtitle, text, url=None, id=None):
    self.example_dict = {}
    self.set_id(self.new_id(id))
    self.set_url(url)
    self.set_domain(domain)
    self.set_source(source)
    self.set_title(title)
    self.set_subtitle(subtitle)
    self.set_text(text)
    self.set_example_knowledge([])
    self.set_body([])
    self.set_specification([])

  def to_query_str(self):
    s = "" 
    s += self.to_body_str() + "\n"
    s += self.to_spec_str() + "\n"
    # LogMessage.write("example_with_spec=" + str(len(s)))
    return s
  
  def to_body_str(self):
    s = str(self.get_title()) + ". " 
    for section in self.get_body():
        s += str(section.heading) + ". "
        for element in section.elements:
            s += str(element.text) + ". "
    return s
    
  def to_spec_str(self):
    s = ""
    for section in self.get_specification():
        heading = section[0]
        elements = section[1]  
        s += str(heading) + ":" + "\n"         
        for k, v in elements.items():
          s += " " + str(k).strip() + ": " + str(v).strip() + ". " + "\n"
        s += "\n"    
    return s

  def __str__(self):
    s = "example=>" + str(self.get_title()) + "\t" + str(self.get_knowledge()) + "\n"
    for section in self.get_body():
        s += "\t" + "-section=>" + str(section.heading) + str(section.knowledge) + "\n"
        for element in section.elements:
            s += "\t\t" + "--element=>" + str(element.knowledge) + "\n"
    return s

  def __repr__(self):
    return str(self.example_dict)

  def toJSON(self):
    return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

  ### ID
  def new_id(self, id):
    if id == None:
      id = str(uuid.uuid1())
    return id

  def set_id(self, text):
    self.example_dict["id"] = text

  def get_id(self):
      return self.example_dict["id"]

  ### SET
  def set_source(self, text):
    self.example_dict["source"] = text

  def set_title(self, text):
    self.example_dict["title"] = text

  def set_subtitle(self, text):
    self.example_dict["subtitle"] = text

  def set_text(self, text):
    self.example_dict["text"] = text

  def set_example_knowledge(self, knowledge):
    self.example_dict[ContentExample.KNOWLEDGE_KEY] = self.valid_knowledge(knowledge)

  def set_url(self, text):
    self.example_dict[ContentExample.URL_KEY] = text

  def set_specification(self, spec):
    self.example_dict[ContentExample.SPECIFICATION_KEY] = spec

  def set_body(self, body):
    self.example_dict[ContentExample.BODY_KEY] = body 

  def set_price(self, price):
    self.example_dict[ContentExample.PRICE_KEY] = price 

  def set_code(self, code):
    self.example_dict[ContentExample.PRODUCT_CODE] = code 

  def set_images(self, images):
    self.example_dict[ContentExample.PRODUCT_IMAGES] = images 


  ### GET
  def get_dict(self):
     return self.example_dict
  
  def set_domain(self, text):
    self.example_dict["domain"] = text

  def get_domain(self):
    return self.example_dict["domain"]

  def get_source(self):
    return self.example_dict["source"]

  def get_title(self):
    return self.example_dict["title"]

  def get_subtitle(self):
    return self.example_dict["subtitle"]

  def get_text(self):
    return self.example_dict["text"]

  def get_knowledge(self):
    return self.example_dict[ContentExample.KNOWLEDGE_KEY]

  def get_url(self):
    return self.example_dict[ContentExample.URL_KEY]

  def get_body(self):
    return self.example_dict[ContentExample.BODY_KEY]

  def get_specification(self):
    return self.example_dict[ContentExample.SPECIFICATION_KEY]
  
  def get_price(self):
     return self.example_dict[ContentExample.PRICE_KEY]

  def get_code(self):
     return self.example_dict[ContentExample.PRODUCT_CODE]

  def get_images(self):
     return self.example_dict[ContentExample.PRODUCT_IMAGES]


  def get_sections(self):
    return self.get_body()

  def get_section(self, id):
    section = None
    for item in self.get_body():
      if item.id == id:
        section = item
    return section

  def get_element(self, section, id):
    element = None
    for item in section.elements:
      if item.id == id:
        element = item
    return element

  def get_elements(self):
    elements = []
    sections = self.get_sections()
    for section in sections:
      for item in section.elements:
         elements.append(item)
    return elements

  def add_section(self, heading="", id=None):
    '''
    ContentSection = namedtuple('ContentSection', ['heading', 'elements', 'knowledge', 'id'])
    SectionElement = namedtuple('SectionElement', ['text', 'knowledge', 'id'])
    '''
    if id is None:
        id = str(uuid.uuid1())
    elements = []
    knowledge = []
    section = ContentSection(heading, elements, knowledge, id)
    self.get_body().append(section)
    return id
  
  def add_spec_section(self, spec_section):
     '''
     tv1_spec_category = SpecSection("TELEVISION CATEGORY", {"Television Type": "Flat Panel"})
     add_spec_section(tv1_spec_category)      
     '''
     self.get_spec().append(spec_section)

  def add_section_element(self, section_id, text, id=""):
    if id == "":
        id = str(uuid.uuid1())
    section = self.get_section(section_id)
    knowledge = []
    element = SectionElement(text, knowledge, id)
    section.elements.append(element)

  ### ADD KNOWLEDGE
  def add_example_knowledge(self, knowledge=[], is_log = False):
    prior = set(self.get_knowledge())
    knowledge = knowledge.union(prior)
    self.set_example_knowledge(list(knowledge))

  def add_section_knowledge(self, section, knowledge=[], is_log=False):
    prior = set(section.knowledge)
    knowledge = knowledge.union(prior)
    section.knowledge.clear()
    knowledge = self.valid_knowledge(knowledge)
    section.knowledge.extend(list(knowledge))

  def add_element_knowledge(self, element, knowledge=[], is_log=False):
    prior = set(element.knowledge)
    knowledge = knowledge.union(prior)
    element.knowledge.clear()
    knowledge = self.valid_knowledge(knowledge)
    element.knowledge.extend(list(knowledge))

  ### KNOWLEDGE
  def get_all_knowledge(self):
      knowledge = set()
      knowledge.update(self.get_knowledge())
      for section in self.get_body():
          knowledge.update(section.knowledge)
          for element in section.elements:
              knowledge.update(element.knowledge)
      return self.valid_knowledge(knowledge)
  
  def valid_knowledge(self, knowledge):
      knowledge = list(set(knowledge))
      knowledge = [w.strip().lower() for w in knowledge]
      knowledge = [w for w in knowledge if w != '' and w != ' ']
      return sorted(knowledge)


class TagConfig():

    def __init__(self,
                is_source_primary,
                is_example_title_primary, is_example_subtitle_primary, is_example_text_primary,
                is_section_heading_primary, is_element_text_primary,
                primary_tagging_func,
                is_source_secondary,
                is_example_title_secondary, is_example_subtitle_secondary, is_example_text_secondary,
                is_section_heading_secondary, is_element_text_secondary,
                secondary_tagging_func):
      # primary
      self.is_source_primary = is_source_primary
      self.is_example_title_primary = is_example_title_primary
      self.is_example_subtitle_primary = is_example_subtitle_primary
      self.is_example_text_primary = is_example_text_primary
      self.is_section_heading_primary = is_section_heading_primary
      self.is_element_text_primary = is_element_text_primary
      self.primary_tagging_func = primary_tagging_func
      # secondary
      self.is_source_secondary = is_source_secondary
      self.is_example_title_secondary = is_example_title_secondary
      self.is_example_subtitle_secondary = is_example_subtitle_secondary
      self.is_example_text_secondary = is_example_text_secondary
      self.is_section_heading_secondary = is_section_heading_secondary
      self.is_element_text_secondary = is_element_text_secondary
      self.secondary_tagging_func = secondary_tagging_func

    def get_primary_text(self, example):
        texts = []
        # top
        if self.is_example_title_primary:
            texts.append(example.get_title())
        if self.is_example_subtitle_primary:
            texts.append(example.get_subtitle())
        if self.is_example_text_primary:
            texts.append(example.get_text())
        # section
        for section in example.get_body():
            if self.is_section_heading_primary:
                texts.append(section.heading)
            for element in section.elements:
                if self.is_element_text_primary:
                    texts.append(element.text)
        return texts

    def get_secondary_text(self, example):
        texts = []
        # top
        if self.is_example_title_secondary:
            texts.append(example.get_title())
        if self.is_example_subtitle_secondary:
            texts.append(example.get_subtitle())
        if self.is_example_text_secondary:
            texts.append(example.get_text())
        # section
        for section in example.get_body():
            if self.is_section_heading_secondary:
                texts.append(section.heading)
            for element in section.elements:
                if self.is_element_text_secondary:
                    texts.append(element.text)
        return texts

    def get_example_text(self, example):
        texts = []
        texts.append(example.get_title())
        texts.append(example.get_subtitle())
        texts.append(example.get_text())
        return texts

    def get_section_text(self, section):
        texts = []
        texts.append(section.heading)
        return texts

    def get_element_text(self, element):
        texts = []
        texts.append(element.text)
        return texts
    
    
class GiftDetails():
    ### domain, source, title, subtitle, text, url, example_id, price, images
    # {'title': 'Aristocrat 32 Ltrs Green Medium Backpack',
    #  'price': 1575,
    #  'uri': 'https://www.tatacliq.com/p-MP000000015359169',
    #  'image_url': 'https://img.tatacliq.com/images/i8/437Wx649H/MP000000015359169_437Wx649H_202211210256201.jpeg',
    #  'description': 'Bag Type : Backpacks, Capacity : 32litres, Closure Type : Zip, Color : Green, Height : 34.5cm, Length : 25.5cm, Material Type : Polyester, No of Compartments : 3, Size : Medium, Strap Type : Adjustable, Width : 49cm, ',
    #  'master_output': {'id': 'TATACLIQ-PRIMARY-BPTIAGHGRN-Aristocrat',
    #   'product': {'name': 'projects/473979811399/locations/global/catalogs/default_catalog/branches/0/products/TATACLIQ-PRIMARY-BPTIAGHGRN-Aristocrat',
    #    'title': 'Aristocrat 32 Ltrs Green Medium Backpack',
    #    'brands': ['Aristocrat'],
    #    'attributes': {'bu_name': {'text': ['TATACLIQ PRIMARY']}},
    #    'uri': 'https://www.tatacliq.com/p-MP000000015359169',
    #    'variants': [{'name': 'projects/473979811399/locations/global/catalogs/default_catalog/branches/0/products/TATACLIQ-MP000000015359169',
    #      'id': 'TATACLIQ-MP000000015359169',
    #      'type': 'VARIANT',
    #      'title': 'Aristocrat 32 Ltrs Green Medium Backpack',
    #      'brands': ['Aristocrat'],
    #      'attributes': {'l1_category_h': {'text': ['Accessories>Mens Bags'],
    #        'searchable': False,
    #        'indexable': False},
    #       'l2_category': {'text': ['Backpacks'],
    #        'searchable': False,
    #        'indexable': False},
    #       'l0_category_h': {'text': ['Accessories'],
    #        'searchable': False,
    #        'indexable': False},
    #       'expireTime': {'text': ['2025-11-17T07:00:00Z'],
    #        'searchable': False,
    #        'indexable': False},
    #       'img_url': {'text': ['https://img.tatacliq.com/images/i8/437Wx649H/MP000000015359169_437Wx649H_202211210256201.jpeg'],
    #        'searchable': False,
    #        'indexable': False},
    #       'l3_category_h': {'text': ['Accessories>Mens Bags>Backpacks>Backpacks'],
    #        'searchable': False,
    #        'indexable': False},
    #       'brands': {'text': ['Aristocrat'],
    #        'searchable': False,
    #        'indexable': False},
    #       'l0_category': {'text': ['Accessories'],
    #        'searchable': False,
    #        'indexable': False},
    #       'catCode': {'text': ['MSH16'], 'searchable': False, 'indexable': False},
    #       'l1_category': {'text': ['Mens Bags'],
    #        'searchable': False,
    #        'indexable': False},
    #       'l3_category': {'text': ['Backpacks'],
    #        'searchable': False,
    #        'indexable': False},
    #       'Hex_Code': {'text': ['Green>#00FF00'],
    #        'searchable': False,
    #        'indexable': False},
    #       'availability': {'text': ['IN_STOCK'],
    #        'searchable': False,
    #        'indexable': False},
    #       'colors': {'text': ['Green'], 'searchable': False, 'indexable': False},
    #       'expireStatus': {'text': ['No'],
    #        'searchable': False,
    #        'indexable': False},
    #       'bu_name': {'text': ['TATACLIQ MARKETPLACE'],
    #        'searchable': False,
    #        'indexable': False},
    #       'neu_category': {'text': ['Fashion, Fitness, Beauty'],
    #        'searchable': False,
    #        'indexable': False},
    #       'categories': {'text': ['Sales>Accessories>Mens Bags>Backpacks>Backpacks'],
    #        'searchable': False,
    #        'indexable': False},
    #       'l2_category_h': {'text': ['Accessories>Mens Bags>Backpacks'],
    #        'searchable': False,
    #        'indexable': False}},
    #      'priceInfo': {'currencyCode': 'INR',
    #       'price': 1575,
    #       'originalPrice': 3500},
    #      'availability': 'IN_STOCK',
    #      'uri': 'https://www.tatacliq.com/p-MP000000015359169',
    #      'images': [{'uri': 'https://img.tatacliq.com/images/i8/437Wx649H/MP000000015359169_437Wx649H_202211210256201.jpeg'}],
    #      'colorInfo': {'colors': ['Green']}}]},
    #   'matchingVariantCount': 1,
    #   'file': 'bag-mens_backpacks.json'}}
    def __init__(self):
        pass

    def get_domain(corpus_example):
        return GiftDetails.get_product_id(corpus_example).split("-")[0]

    def get_source(corpus_example):
        return "DATA_DUMP"

    def get_product_id(corpus_example):
        return corpus_example['master_output']['id']

    def get_example_id(corpus_example):
        return GiftDetails.get_product_id(corpus_example)

    def get_id(corpus_example):
        return GiftDetails.get_product_id(corpus_example)

    def get_title(corpus_example):
        return corpus_example['title']

    def get_subtitle(corpus_example):
        return ""

    def get_text(corpus_example):
        return ""

    def get_price(corpus_example):
        return corpus_example['price']

    def get_url(corpus_example):
        return corpus_example['uri']

    def get_images(corpus_example):
        return corpus_example['image_url']

    def get_description(corpus_example):
        return corpus_example['description']

    def get_specification(corpus_example):
        return GiftDetails.get_description(corpus_example)   
    

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


class GiftDataset():

    def read_data(self, dir_path="./"):
        ### FILES
        file_names = JsonReader.list_files(dir_path)
        print(file_names)
        ### DATA
        return [JsonReader.read_file(file_name, dir_path) for file_name in file_names]


class GiftReader():

    def __init__(self, product_details = GiftDetails()):
        self.product_details = product_details

    def read_examples(self, corpus_list):
        example_corpus = {}
        unique_titles = set()
        for content_json in corpus_list:
            try:
                ### form
                corpus_example = GiftReader.get_example(content_json)
                ### save
                product_id = corpus_example.get_id()
                if product_id not in unique_titles:
                    example_corpus[product_id] = corpus_example
                    unique_titles.add(product_id)
                    # LogMessage.write("READ_EXAMPLE=" + str(k) + " " + str(v))
            except Exception as e:
                LogMessage.write("EXAMPLE_READER_ERROR=" + str(e) + " " + str(k))
        return example_corpus

    def get_example(content_json):
        ### top
        domain = GiftDetails.get_domain(content_json)
        source = GiftDetails.get_source(content_json)
        title = GiftDetails.get_title(content_json)
        subtitle = GiftDetails.get_subtitle(content_json)
        text = GiftDetails.get_text(content_json)
        example_id = GiftDetails.get_id(content_json)
        url = GiftDetails.get_url(content_json)
        descripion = GiftDetails.get_description(content_json)
        # example_knowledge = content_example['knowledge']

        ### example
        example = ContentExample(domain, source, title, subtitle, text, url, example_id)
        example.set_specification(descripion)
        ### body
        # try:
        #     body = GiftReader.get_body(content_json)
        #     GiftReader.set_body(example, body)
        # except:
        #     pass
        ### spec
        # try:
        #     specification = GiftReader.get_spec(content_json)
        #     example.set_specification(specification)
        # except:
        #     pass

        return example

class GiftRetriever():

    def __init__(self):
        dataset = GiftDataset() 
        self.master_json = dataset.read_data(dir_path="/content/drive/MyDrive/TataLLM/GiftReader/")

    def get_example(self):
        # return GiftReader.get_example(master_json[0][1])        
        pass 

# class ExampleReader():

#     def __init__(self, product_details):
#         self.product_details = product_details

#     def read_examples(self, corpus_dict):
#         example_corpus = {}
#         unique_titles = set()
#         for k, v in corpus_dict.items():
#             try:
#                 # form
#                 corpus_example = ExampleReader.get_example(v)
#                 product_id = ExampleReader.get_product_id(corpus_example)
#                 example_price = self.product_details.get_price(product_id)
#                 corpus_example.set_price(example_price)
#                 example_images = self.product_details.get_images(product_id)
#                 corpus_example.set_images(example_images)
#                 # save
#                 example_title = corpus_example.get_title() 
#                 if product_id not in unique_titles:
#                     example_corpus[k] = corpus_example
#                     unique_titles.add(product_id)
#                     # LogMessage.write("READ_EXAMPLE=" + str(k) + " " + str(v))
#             except Exception as e:
#                 LogMessage.write("EXAMPLE_READER_ERROR=" + str(e) + " " + str(k))
#         return example_corpus

#     def get_product_id(corpus_example):
#         url = corpus_example.get_url()
#         parts = url.split("/")
#         return parts[-1]

#     def get_example(content_json):
#         ### top
#         domain = ExampleReader.get_domain(content_json)
#         source = ExampleReader.get_source(content_json)
#         title = ExampleReader.get_title(content_json)
#         subtitle = ExampleReader.get_subtitle(content_json)
#         text = ExampleReader.get_text(content_json)
#         example_id = ExampleReader.get_id(content_json)
#         url = ExampleReader.get_url(content_json)
#         # example_knowledge = content_example['knowledge']

#         ### example
#         example = ContentExample(domain, source, title, subtitle, text, url, example_id)
#         ### body
#         try:
#             body = ExampleReader.get_body(content_json)
#             ExampleReader.set_body(example, body)
#         except:
#             pass
#         ### spec
#         try:
#             specification = ExampleReader.get_spec(content_json)
#             example.set_specification(specification)
#         except:
#             pass

#         return example
        
#     def get_domain(content_json):
#         try:
#             return content_json['domain'].strip()
#         except:
#             return ""

#     def get_source(content_json):
#         try:
#             return content_json['source'].strip()
#         except:
#             return ""

#     def get_title(content_json):
#         try:
#             return content_json['title'].strip()
#         except:
#             return ""

#     def get_subtitle(content_json):
#         try:
#             return content_json['subtitle'].strip()
#         except:
#             return ""

#     def get_text(content_json):
#         try:
#             return content_json['text'].strip()
#         except:
#             return ""

#     def get_id(content_json):
#         try:
#             return content_json['id'].strip()
#         except:
#             return ""

#     def get_url(content_json):
#         try:
#             return content_json['url'].strip()
#         except:
#             return ""

#     def get_body(content_json):
#         try:
#             return content_json['body']
#         except:
#             return []

#     def get_spec(content_json):
#         try:
#             return content_json['specification']
#         except:
#             return []

#     def set_body(example, body):
#         for section in body:
#           heading = section[0].strip()
#           elements = section[1]
#           # section_knowledge = section[2]
#           section_id = section[3].strip()
#           example.add_section(heading=heading, id=section_id)

#           for element in elements:
#             element_text = element[0].strip()
#             element_knowledge = element[1]
#             element_id = element[2]
#             example.add_section_element(section_id=section_id, text=element_text, id=element_id)        

    

 

# class GiftTagger():

#     def __init__self():
#         pass

#     def tag(example_corpus):
#         croma_config = CromaText.tag_config(TagProcessor())
#         tag_croma = TagCorpus(croma_config, is_log=True)
#         tag_croma.add_and_tag(example_corpus.values())


