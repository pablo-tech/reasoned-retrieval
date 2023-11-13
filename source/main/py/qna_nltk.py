import nltk
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords
from nltk.corpus import words
from nltk.stem.lancaster import LancasterStemmer 
from nltk.util import ngrams


class NltkProcessor():

    def __init__(self):
        self.nltk_tokenizer = RegexpTokenizer(r'\w+')
        self.nltk_stemmer = LancasterStemmer()
        self.stop_words = set(stopwords.words('english'))
        self.english_words = set(words.words())

    ### TOKENIZE
    def tokenize_text(self, text):
        return self.nltk_tokenizer.tokenize(text)
    
    ### TAG
    def word_tokenize(self, sentence):
        return nltk.word_tokenize(sentence)
    
    def part_of_speech(self, tokens):
        return nltk.pos_tag(tokens)
    
    def n_gram(self, text, n = 2):
        return list(ngrams(text.split(" "), n))
    
    ### STEM
    def stem_word(self, word):
        return self.nltk_stemmer.stem(word)

    def stem_words(self, words):
      stemmed = []
      for word in words:
          stemmed.append(self.stem_word(word))
      return stemmed

    ### PUNCTUATION
    def remove_punctuation(self, text):
      try:
          text = text.strip().lower()
          words = self.nltk_tokenizer.tokenize(text)
          return words
      except Exception as e:
          print(text + str(e))
          return []
      
    ### STOP
    def is_stop_word(self, word):
        return word in self.stop_words
