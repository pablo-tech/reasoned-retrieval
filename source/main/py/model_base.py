import openai
import os

from langchain import PromptTemplate
from langchain import OpenAI
from langchain.chat_models import ChatOpenAI

import numpy as np
import pandas as pd
import google.generativeai as palm
import getpass

from transformers import AutoTokenizer
import transformers
import torch

from model_huggingface import HuggingFaceAuth
from model_huggingface import HuggingFaceRemote


class OpenaiBase():

    def __init__(self):
        self.api_key = "95a179d989cd4aeb84d36edb2fc8991a"

        self.api_version = "2023-07-01-preview" # "2023-03-15-preview"
        self.api_type = "azure"
        self.api_base = "https://tdl-chatbot.openai.azure.com/"

        openai.api_version = self.api_version
        openai.api_type = self.api_type
        openai.api_base = self.api_base
        openai.api_key = self.api_key

        os.environ["OPENAI_API_VERSION"] = self.api_version
        os.environ["OPENAI_API_TYPE"] = self.api_type
        os.environ["OPENAI_API_BASE"] = self.api_base
        os.environ["OPENAI_API_KEY"] = self.api_key

    def inference_llm_30(self, temperature=0, max_tokens = 256):
        return OpenAI(openai_api_key=self.api_key,
                      model_name='text-davinci-003',
                      engine="bot-davinci",
                      temperature=temperature,
                      max_tokens=max_tokens)

        # AzureOpenAI(openai_api_key=api_key,
        #             model_name='text-davinci-003',
        #             engine="bot-davinci",
        #             temperature=0,
        #             max_tokens = 256)

    def chat_llm_40(self, temperature=0, max_tokens = 256):
        return ChatOpenAI(openai_api_key=self.api_key,
                          engine="tdl-gpt-4",
                          temperature=temperature,
                          max_tokens=max_tokens)


class GoogleBase():

    def __init__(self):
        self.palm_api_key="AIzaSyDO6QXdAxqyex0pKqmfUUEFYuV0CvjC-WU"
        # palm_api_key = getpass.getpass(prompt='Enter your PaLM API key: ')
        palm.configure(api_key=self.palm_api_key)

    def palm_llm_2(self, prompt):
        completion = palm.generate_text(
            model="models/text-bison-001",
            prompt=prompt,
            temperature=0.1,
            # The maximum length of the response
            max_output_tokens=800,
        )
        return completion.result


class MetaBase():

    def __init__(self, model_name):
        HuggingFaceAuth()
        self.pipeline = self.get_pipeline(model_name)

    def get_pipeline(self, model_name):
        tokenizer=AutoTokenizer.from_pretrained(model_name)
        return transformers.pipeline(
            "text-generation",
            model=model_name,
            tokenizer=tokenizer,
            torch_dtype=torch.bfloat16,
            trust_remote_code=True,
            device_map="auto",
            max_length=1000,
            do_sample=True,
            top_k=10,
            num_return_sequences=1,
            eos_token_id=tokenizer.eos_token_id,
            token=os.environ["HUGGINGFACEHUB_API_TOKEN"])
    
    def invoke(self, prompt):
        txt = self.pipeline(prompt)[0]['generated_text']
        txts = txt.split("Answer:")
        return txts[1].strip()


class llama2_7b(MetaBase):
    def __init__(self):
        super().__init__("meta-llama/Llama-2-7b")
    

class lama2_7b_chat(MetaBase):
    def __init__(self):
        super().__init__("meta-llama/Llama-2-7b-chat")


class llama2_7b_hf(MetaBase):
    def __init__(self):
        super().__init__("meta-llama/Llama-2-7b-hf")


class llama2_7b_chat_hf(MetaBase):
    def __init__(self):
        super().__init__("meta-llama/Llama-2-7b-chat-hf")


class llama2_13b(MetaBase):
    def __init__(self):
        super().__init__("meta-llama/Llama-2-13b")
    

class llama2_13b_chat(MetaBase):
    def __init__(self):
        super().__init__("meta-llama/Llama-2-13b-chat")


class llama2_13b_hf(MetaBase):
    def __init__(self):
        super().__init__("meta-llama/Llama-2-13b-hf")


class llama2_13b_chat_hf(MetaBase):
    def __init__(self):
        super().__init__("meta-llama/Llama-2-13b-chat-hf")


class LlmInfernce():

  def __init__(self, llm_generator, human_key, ai_key):
      self.llm_generator = llm_generator
      template = human_key + ": {question}" + "\n"
      template += ai_key + ":"
      self.prompt_template = PromptTemplate(template=template, input_variables=["question"])

  def question_answer(self, question, model_params):
      inferred = self.llm_generator.chain_forward(inference_context={"question": question},
                                                  prompt_template=self.prompt_template,
                                                  model_params=model_params)
      inferred = inferred.split("###")[0]
      return inferred


class FlanInference(LlmInfernce):

  def __init__(self, llm_generator):
      super().__init__(llm_generator, "Question", "Answer")


class FlanXxl(FlanInference):

    def __init__(self):
        super().__init__(llm_generator=HuggingFaceRemote(repo_id="google/flan-t5-xxl"))
        
    def invoke(self, prompt):
        return self.question_answer(question=prompt,
                                    model_params={"temperature": 0.5,
                                                  "repetition_penalty": 1.1})      


