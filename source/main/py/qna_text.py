import sys
import time
import numpy as np

from qna_nltk import NltkProcessor


class TextNormalizer():
    # https://stackoverflow.com/questions/9227527/are-there-any-classes-in-nltk-for-text-normalizing-and-canonizing
    def __init__(self):
        self.abbreviations = { "tv": "television",
                               "tvs": "television",
                               "ac": "air conditioner",
                               "acs": "air conditioner"}
        self.repetitve = set(self.abbreviations.keys()).union(set(self.abbreviations.values()))

    def expand_abbreviation(self, txt):
        parts = []
        for w in txt.split(" "):
            if w.lower() not in self.abbreviations:
                parts.append(w)
            else:
                parts.append(self.abbreviations[w.lower()])
        return " ".join(parts)
    
    def is_repetitive(self, txt):
        return txt in self.repetitve
    
    def remove_repetitive(self, txt):
        parts = []
        for w in txt.split(" "):
            if self.is_repetitive(w.lower()):
                parts.append(w)
        return " ".join(parts)        
            


class PartOfSpeech():

    def __init__(self):
        self.noun_part = ['NNP', # proper noun, singular (sarah)
                          'NN',  # noun, singular (cat, tree)
                          'NNS'  # noun plural (desks) 
                         ]
        self.quant_part = ['CD', # cardinal digit
                           'JJ'  # adjective (large)
                          ]
        self.text_processor = NltkProcessor()

    def scaled_nouns(self, sentence):
        word_tokens = self.pos_tokens(sentence)    
        word_tokens = self.reduce_nouns(word_tokens)   
        word_tokens = [ word_token[0] for word_token in word_tokens ]
        # LogMessage.out("scaled_nouns=" + str(word_tokens))
        return word_tokens
    
    def found_adjectives(self, sentence):
        word_tokens = self.pos_tokens(sentence)    
        word_tokens = [ word_token[0] for word_token in word_tokens if word_token[1] == 'JJ']
        return word_tokens
    
    def pos_tokens(self, sentence):
        # LogMessage.out("sentence=" + str(sentence))
        tokens = self.text_processor.word_tokenize(sentence)
        word_tokens = self.text_processor.part_of_speech(tokens)
        # LogMessage.out("word_tokens=" + str(word_tokens))   
        return word_tokens

    def reduce_nouns(self, word_tags, min_length = 2):
        reduced = []
        separator = " "
        for i in range(len(word_tags)):
            word_tag_curr = word_tags[i]
            curr_word = word_tag_curr[0]
            curr_label = word_tag_curr[1]
            curr_is_scalar, _ = TextParser.is_scalar(word_tag_curr[0])
            # scaled noun
            if curr_is_scalar and i+1<len(word_tags):
                word_tag_next = word_tags[i+1]
                next_word = word_tag_next[0]
                next_label = word_tag_next[1]
                if len(next_word) >= min_length:
                    if curr_label in self.quant_part and next_label in self.noun_part or\
                       curr_label in self.quant_part and next_label in self.quant_part:
                            value = curr_word.lower() + separator + next_word.lower()
                            together = (value, 'NNS')  
                            reduced.append(together)
                            i += 2
            # noun
            elif len(curr_word) >= min_length:
                if curr_label in self.noun_part:
                    value = curr_word.lower()
                    together = (value, 'NN')
                    reduced.append(together)
        return reduced


class TextParser():
        
    def get_hash(words):
        return tuple(sorted(list(words)))

    def answer_punctuation(text):
        text = text.strip()
        l = len(text)-1
        if l >= 0 and text[l] == ".":
            text = text[:-1]
        return text

    def combine_scalar(words):
      # print("the_words=" + str(words))      
      combined = []
      prev_word = ""
      for word in words:
          try:
              is_prev_scalar, prev_value = TextParser.is_scalar(prev_word)
              is_curr_scalar, curr_value = TextParser.is_scalar(word)
              if is_prev_scalar and prev_value < 1000 and not is_curr_scalar:
                  combined.remove(prev_word)
                  combo = prev_word + " " + word
                  combined.append(combo)
              else:
                  combined.append(word)
              prev_word = word
          except Exception as e:
              print("COMBINATION_EXCEPTION=" + str(word) + "\t" + str(e))        
      # print("words_combined=" + str(combined))
      return set(combined)

    def is_scalar(n):
        try:
            float(n)
        except ValueError:
            return False, None
        else:
            return True, float(n)  
