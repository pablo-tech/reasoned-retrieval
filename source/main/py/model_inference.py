from langchain import PromptTemplate

from llm_huggingface import HuggingFaceRemote


class LlmInfernce():

  def __init__(self, llm_generator, human_key, ai_key):
      self.llm_generator = llm_generator
      template = human_key + ": {question}" + "\n"
      template += ai_key + ":"
      self.prompt_template = PromptTemplate(template=template, input_variables=["question"])

  def question_answer(self, questions, model_params):
      for qna in questions:
          question = qna["user_question"]
          answer = qna["agent_answer"]
          inferred = self.llm_generator.chain_forward(inference_context={"question": question},
                                                      prompt_template=self.prompt_template,
                                                      model_params=model_params)
          inferred = inferred.split("###")[0]
          print(f"Q: {question} \nA (actual): {answer} \nA (inferred): {inferred} \n--")


class LlamaInference(LlmInfernce):

  def __init__(self, llm_generator):
      super().__init__(llm_generator, "### Human", "### Assistant")


class FlanInference(LlmInfernce):

  def __init__(self, llm_generator):
      super().__init__(llm_generator, "Question", "Answer")



from llm_huggingface import HuggingFaceRemote

from langchain.chains.question_answering import load_qa_chain
# from langchain.chat_models import ChatOpenAI
# from langchain.llms import OpenAI

from collections import defaultdict


class LlmRetriever():

  def __init__(self,
               llm_generator,
               vector_db):
      self.llm_generator = llm_generator
      self.vector_db = vector_db

  def new_chain(self, chain_type, model_params):
      llm = self.llm_generator.new_llm(model_params)
      return load_qa_chain(llm=llm,
                           chain_type=chain_type)

  def similarity_search_func(self):
      store = self.vector_db.lang_store()
      return store.similarity_search

  def max_marginal_relevance_search_func(self):
      store = self.vector_db.lang_store()
      return store.max_marginal_relevance_search

  def question_answer(self,
                      query,
                      k,
                      model_params,
                      search_func,
                      chain_type='refine', # stuff, map_reduce, refine, map-rerank
                      ):
      docs = search_func(query, k)
      qa_chain = self.new_chain(chain_type, model_params)
      answer = qa_chain({'input_documents': docs, 'question': query})
      sources = defaultdict(set)
      for doc in answer['input_documents']:
          sources[doc.metadata['source']].add(int(doc.metadata['chunk']))
      answer['sources'] = sources
      return answer