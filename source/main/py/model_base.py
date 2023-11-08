import openai
import os

from langchain import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.llms import AzureOpenAI
# from langchain.llms import AzureChatOpenAI

import numpy as np
import pandas as pd
import google.generativeai as palm
import getpass


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
