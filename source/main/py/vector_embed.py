# https://bpemb.h-its.org/
from bpemb import BPEmb
# https://www.sbert.net/docs/pretrained_models.html
from sentence_transformers import SentenceTransformer
import numpy as np


class BytePairEmbed():

  def __init__(self, bpemb_en):
    self.bpemb_en = bpemb_en

  def embed(self, sentences):
    pools = []
    for sentence in sentences:
      subwords = self.bpemb_en.encode(sentence)
      ids = self.bpemb_en.encode_ids(sentence)
      embeds = self.bpemb_en.vectors[ids]
      try:
        v1 = np.array(embeds[0])
        pool = v1
        for i in range(1, len(embeds)):
          v_i = np.array(embeds[i])
          pool = np.add(pool, v_i)
        pool /= len(embeds)
      except:
        pool = np.zeros((100))
      pools.append(pool)
    return pools


class EmbeddingProcessor():
  sentence_embedding_model = SentenceTransformer('all-mpnet-base-v2')
  bytepair_embedding_model = BytePairEmbed(BPEmb(lang="en"))

  def word_encode(words):
      return EmbeddingProcessor.bytepair_embedding_model.embed(words)

  def sentence_encode(sentences):
    return EmbeddingProcessor.sentence_embedding_model.encode(sentences)
  

class BytePairEmbedding():

  def embed_documents(documents):
      vectors = []
      for doc in documents:
          vectors.append(BytePairEmbedding.embed_query(doc))
      return vectors

  def embed_query(text):
      return EmbeddingProcessor.sentence_encode(text)  



        