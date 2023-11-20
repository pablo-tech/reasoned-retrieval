import openai
import os

from langchain import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.llms import GooglePalm
from langchain.llms import HuggingFacePipeline
from langchain import HuggingFaceHub

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

    def chat_llm_40(self, temperature=0, max_tokens = 256):
        return ChatOpenAI(openai_api_key=self.api_key,
                          engine="tdl-gpt-4",
                          temperature=temperature,
                          max_tokens=max_tokens)
    
    # def chat_llm_40_turbo(self, temperature=0, max_tokens = 256):
    #     return ChatOpenAI(openai_api_key=self.api_key,
    #                       engine="gpt-4-1106-preview",
    #                       temperature=temperature,
    #                       max_tokens=max_tokens)
    

class GoogleBase():

    def __init__(self):
        HuggingFaceAuth()

    def palm2(self):
        return GooglePalm(google_api_key="AIzaSyDO6QXdAxqyex0pKqmfUUEFYuV0CvjC-WU",
                          model_kwargs={'temperature':0.5})    

    def flan_xxl(self):
        return HuggingFaceHub(repo_id="google/flan-t5-xxl",
                              model_kwargs={'temperature':0.5})


class MetaBase():

    def __init__(self):
        HuggingFaceAuth()

    def llama2_7b_chat_hf(self, 
                          model_name="meta-llama/Llama-2-7b-chat-hf",
                          model_kwargs={'temperature':0.5}):
        
        tokenizer=AutoTokenizer.from_pretrained(model_name,
                                                token=os.environ["HUGGINGFACEHUB_API_TOKEN"])
        pipeline = transformers.pipeline(
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
        
        return HuggingFacePipeline(pipeline=pipeline, 
                                   model_kwargs=model_kwargs)

