from collections import defaultdict

from qna_text import TextParser, PartOfSpeech
from qna_entity import BrandRecognition
from qna_croma_text import CromaText
from qna_text import TextNormalizer
from qna_nltk import NltkProcessor
    

# class TagCorpus():

#     primary_global_tokens = defaultdict(set)
#     secondary_global_tokens = defaultdict(set)

#     def __init__(self, corpus_config, is_log):
#         self.corpus_config = corpus_config
#         self.is_log = is_log

#     def add_and_tag(self, examples):
#         try:
#             self.add_items(examples)
#             self.tag_examples(examples)
#             self.print_knowledge(examples)
#         except Exception as e:
#             print("TAGGER_ERROR=" + str(e))

#     ### GETTER
#     def get_domains(self):
#         return self.primary_global_tokens.keys()

#     ### TOKEN
#     def add_primary_tokens(self, texts, domain):
#         for text in texts:
#             words = self.corpus_config.primary_tagging_func(text)
#             self.primary_global_tokens[domain].update(words)

#     def get_primary_tokens(self, domain):
#         return self.primary_global_tokens[domain]

#     def add_secondary_tokens(self, texts, domain):
#         for text in texts:
#             words = self.corpus_config.secondary_tagging_func(text)
#             self.secondary_global_tokens[domain].update(words)

#     def get_secondary_tokens(self, domain):
#         return self.secondary_global_tokens[domain]

#     def check_belonging(self, words, domain):
#         for word in words:
#             print(word +
#                   "\t" + "in_primary=" + str(word in self.primary_global_tokens[domain]),
#                   "\t" + "in_secondary=" + str(word in self.secondary_global_tokens[domain]))

#     def add_to_domain(self, words, name):
#         for word in words:
#             self.primary_global_tokens[name].add(word)

#     ### TEXT IN EXAMPLE
#     def add_items(self, examples):
#         for example in examples:
#             try:
#                 self.add_item(example)
#             except:
#                 print("ADD_ITEM_ERROR=" + str(example))

#     def add_item(self, example):
#         domain = example.get_domain()
#         # get text
#         primary_texts = self.corpus_config.get_primary_text(example)
#         secondary_texts = self.corpus_config.get_secondary_text(example)
#         ## collect tags
#         self.add_primary_tokens(primary_texts, domain)
#         self.add_secondary_tokens(secondary_texts, domain)

#     ### TAG IN TEXT
#     def example_tags(self, example, tags):
#         words_in = set()
#         for text in self.corpus_config.get_example_text(example):
#             words_in.update(self.corpus_config.primary_tagging_func(text))
#         words_out = { word for word in words_in if word in tags }
#         return words_out

#     def section_tags(self, section, tags):
#         words_in = set()
#         for text in self.corpus_config.get_section_text(section):
#             words_in.update(self.corpus_config.primary_tagging_func(text))
#         words_out = { word for word in words_in if word in tags }
#         return words_out

#     def element_tags(self, element, tags):
#         words_in = set()
#         for text in self.corpus_config.get_element_text(element):
#             words_in.update(self.corpus_config.secondary_tagging_func(text))
#         words_out = { word for word in words_in if word in tags }
#         return words_out

#     ### TAG
#     def tag_section(self, example, tag_list):
#         knowledge = self.example_tags(example, tag_list)
#         example.add_example_knowledge(knowledge)
#         for section in example.get_body():
#             if self.is_log:
#                 print("tagging_example_sections=" + str(section.heading))
#             knowledge = self.section_tags(section, tag_list)
#             example.add_section_knowledge(section, knowledge)

#     def tag_element(self, example, tag_list):
#         domain = example.get_domain()
#         for section in example.get_body():
#             if self.is_log:
#                 print("tagging_section_elements=" + str(section.heading))
#             for element in section.elements:
#                 knowledge = self.element_tags(element, tag_list)
#                 example.add_element_knowledge(element, knowledge)

#     def tag_domain(self, domain):
#         if self.is_log:
#             print("segregating_domain=" +  str(domain))
#         primary_tokens = self.get_primary_tokens(domain)
#         secondary_tokens = self.get_secondary_tokens(domain).copy()
#         for secondary_token in secondary_tokens:
#             if secondary_token in primary_tokens:
#               self.secondary_global_tokens[domain].remove(secondary_token)

#     def tag_examples(self, examples):
#         ### section: apply primary
#         for example in examples:
#             try:
#                 domain = example.get_domain()
#                 self.tag_section(example, tag_list=self.get_primary_tokens(domain))
#             except Exception as e:
#                 print("PRIMARY_TAG_ERROR=" + str(e))
#         ### clean secondary
#         for domain in self.get_domains():
#             try:
#                 self.tag_domain(domain)
#             except Exception as e:
#                 print("DOMAIN_TAG_ERROR=" + str(e))
#         ### element: apply secondary
#         for example in examples:
#             try:
#                 domain = example.get_domain()
#                 self.tag_element(example, tag_list=self.get_secondary_tokens(domain))
#             except Exception as e:
#                 print("SECONDARY_TAG_ERROR=" + str(e))

#     def print_knowledge(self, examples):
#         for example in examples:
#             try:
#               if self.is_log:
#                 print("tagged>>> " + str(example.get_title()))
#                 # print("tagged>>> " + str(example))
#             except Exception as e:
#                 print("PRINT_KNOWLEDGE_ERROR=" + str(e))
  

class TagProcessor():

    def __init__(self):
        self.part_of_speech = PartOfSpeech()
        self.brand_recognition = BrandRecognition()
        # self.entity_recognition = EntityRecognition()
        self.text_normalizer = TextNormalizer()
        # self.ngram_extraction = NgramExtraction()
        self.remove_punctuation_func = CromaText.remove_punctuation
        self.combine_scalar_func = TextParser.combine_scalar
        self.post_split_remove_func = CromaText.post_split_remove 
        self.nltk_processor = NltkProcessor()

    def tag_words(self, text, min_length=2, is_select_noun=True, is_select_adjective=False):
        # print("tag_words text=" + str(text))
        words_across = set()
        sentences = text.split(". ")
        for sentence in sentences:
            ### cleanup
            sentence = self.remove_punctuation_func(sentence)
            sentence = self.text_normalizer.expand_abbreviation(sentence)
            ### part of speech 
            if is_select_noun:
                pos = set(self.part_of_speech.scaled_nouns(sentence))
                words_across = words_across.union(pos)
            if is_select_adjective:
                pos = set(self.part_of_speech.found_adjectives(sentence))
                words_across = words_across.union(pos)
        ### entities
        entities = set(self.brand_recognition.brand_entities(sentences))
        # entities = set(self.entity_recognition.org_entities(sentences))
        words_across = words_across.union(entities)

        ### cleanup
        words_across = { w for w in words_across if len(w) >= min_length }
        words_across = { w.lower() for w in words_across }
        # print("pos=..." + str(pos))            
        # print("entities=..." + str(entities))
        # print("ngrams=..." + str(ngrams))
        words_across = { word for word in words_across if not self.nltk_processor.is_stop_word(word) }
        # print("words_across=" + str(words_across))
        return words_across
    
