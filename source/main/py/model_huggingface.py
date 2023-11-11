import os
import requests
import json

from langchain import HuggingFaceHub
from langchain import LLMChain
from langchain.llms import HuggingFacePipeline
from langchain.llms import HuggingFaceTextGenInference

import torch
from torch import cuda, bfloat16

import transformers
from transformers import StoppingCriteria, StoppingCriteriaList
from transformers import pipeline


class HuggingFaceAuth():

    def __init__(self,
                 hugging_face_aut = "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"):
        self.set_auth(hugging_face_aut)

    def set_auth(self, auth_token):
        # HUGGINGFACEHUB_API_TOKEN = getpass()
        os.environ["HUGGINGFACEHUB_API_TOKEN"] = auth_token

    def get_auth(self):
        return os.environ["HUGGINGFACEHUB_API_TOKEN"]


class HuggingFaceEnv(HuggingFaceAuth):

    def __init__(self, repo_id):
        super().__init__()
        self.repo_id = repo_id
        self.device = f'cuda:{cuda.current_device()}' if cuda.is_available() else 'cpu'

    def chain_forward(self,
                      inference_context,
                      prompt_template,
                      model_params):
        llm_chain = self.new_chain(prompt_template,
                                   model_params)
        return llm_chain.run(inference_context)

    def get_repo(self):
        return self.repo_id

    def get_device(self):
        return self.device

    

class HuggingFaceRemote(HuggingFaceEnv):

    def __init__(self,
                 repo_id="google/flan-t5-xxl"):
        super().__init__(repo_id)

    def new_llm(self, model_params):
        return HuggingFaceHub(repo_id=self.get_repo(),
                              model_kwargs=model_params)

    def new_chain(self, prompt_template, model_params):
        # https://huggingface.co/docs/api-inference/detailed_parameters
        return LLMChain(prompt=prompt_template, 
                        llm=self.new_llm(model_params))
       

class StopOnTokens(StoppingCriteria):

    def __init__(self, stop_token_ids):
        self.stop_token_ids = stop_token_ids

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        # Check that no <unk> token IDs (0) appear in the stop_token_ids
        for stop_ids in self.stop_token_ids:
            if torch.eq(input_ids[0][-len(stop_ids):], stop_ids).all():
                return True
        return False


class HuggingFaceStoppable(HuggingFaceEnv):

    def __init__(self, repo_id):
        super().__init__(repo_id)
        self.tokenizer = self.new_tokenizer()
        stop_at = [StopOnTokens(self.stop_tokens())]
        self.stopping_criteria = StoppingCriteriaList(stop_at)

    def get_tokenizer(self):
        return self.tokenizer

    def get_stopping(self):
        return self.stopping_criteria

    def stop_tokens(self):
        stop_list = ['\nHuman:', '\n```\n']
        stop_token_ids = [self.get_tokenizer()(x)['input_ids'] for x in stop_list]
        stop_token_ids = [torch.LongTensor(x).to(self.get_device())
                          for x in stop_token_ids]
        return stop_token_ids

    def new_tokenizer(self):
        return transformers.AutoTokenizer.from_pretrained(
            self.get_repo(),
            use_auth_token=self.get_auth()
        )    
    

class StopOnTokens(StoppingCriteria):

    def __init__(self, stop_token_ids):
        self.stop_token_ids = stop_token_ids

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        # Check that no <unk> token IDs (0) appear in the stop_token_ids
        for stop_ids in self.stop_token_ids:
            if torch.eq(input_ids[0][-len(stop_ids):], stop_ids).all():
                return True
        return False


class HuggingFaceStoppable(HuggingFaceEnv):

    def __init__(self, repo_id):
        super().__init__(repo_id)
        self.tokenizer = self.new_tokenizer()
        stop_at = [StopOnTokens(self.stop_tokens())]
        self.stopping_criteria = StoppingCriteriaList(stop_at)

    def get_tokenizer(self):
        return self.tokenizer

    def get_stopping(self):
        return self.stopping_criteria

    def stop_tokens(self):
        stop_list = ['\nHuman:', '\n```\n']
        stop_token_ids = [self.get_tokenizer()(x)['input_ids'] for x in stop_list]
        stop_token_ids = [torch.LongTensor(x).to(self.get_device())
                          for x in stop_token_ids]
        return stop_token_ids

    def new_tokenizer(self):
        return transformers.AutoTokenizer.from_pretrained(
            self.get_repo(),
            use_auth_token=self.get_auth()
        )


class HuggingFaceModel(HuggingFaceStoppable):

    def __init__(self, repo_id):
        super().__init__(repo_id)
        self.model = self.new_model()

    def get_model(self):
        return self.model

    def new_model(self):
        return transformers.AutoModelForCausalLM.from_pretrained(
            self.get_repo(),
            trust_remote_code=True,
            config=self.model_config(),
            quantization_config=self.quantization_config(),
            device_map='auto',
            use_auth_token=self.get_auth()
        )

    def quantization_config(self):
        return transformers.BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type='nf4',
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=bfloat16
        )

    def model_config(self):
        return transformers.AutoConfig.from_pretrained(
            self.repo_id,
            use_auth_token=self.get_auth()
        )


class HuggingFaceWorker(HuggingFaceModel):

    def __init__(self,
                 repo_id,
                 pipe_task):
        super().__init__(repo_id)
        self.pipe_task = pipe_task            


class HuggingFaceGenerator(HuggingFaceWorker):
    # It takes an incomplete text and returns multiple completion outputs
    def __init__(self, repo_id="meta-llama/Llama-2-7b-chat-hf"):
        super().__init__(repo_id, pipe_task='text-generation')

    def forward(self, seed_txt, model_params = {"temperature":0.0,
                                                "max_new_tokens": 512,
                                                "repetition_penalty": 1.1}):
        self.model_params = model_params
        return self.new_worker()(seed_txt)[0]['generated_text']

    def new_worker(self, model_params):
        return transformers.pipeline(model=self.get_model(),
                                     tokenizer=self.get_tokenizer(),
                                     return_full_text=True,  # langchain expects the full text
                                     task=self.pipe_task,
                                     #stopping_criteria=self.get_stopping(),  # without this model rambles during chat
                                     temperature=model_params['temperature'],  # 'randomness' of outputs, 0.0 is the min and 1.0 the max
                                     max_new_tokens=model_params['max_new_tokens'],  # mex number of tokens to generate in the output
                                     repetition_penalty=model_params['repetition_penalty']  # without this output begins repeating
                                     # TODO Provide device={deviceId} to `from_model_id` to use availableGPUs for execution.
                                     )
    
    def new_llm(self, model_params):
        return HuggingFacePipeline(pipeline=self.new_worker(model_params))

    def new_chain(self, prompt_template, model_params):
        # https://huggingface.co/docs/api-inference/detailed_parameters
        # self.model_params = model_params
        return LLMChain(prompt=prompt_template, 
                        llm=self.new_llm(model_params))


class HuggingFaceResponseGenerator(HuggingFaceEnv):

    def __init__(self,
                 repo_id="google/flan-t5-small",
                 model_task="text2text-generation"):
        super().__init__(repo_id)
        self.model_task = model_task

    def new_llm(self, model_params):
        return HuggingFacePipeline.from_model_id(model_id=self.repo_id,
                                                 task=self.model_task,
                                                 # TODO Provide device={deviceId} to `from_model_id` to use availableGPUs for execution.
                                                 # deviceId is -1 (default) for CPU and can be a positive integer associated with CUDA device id.
                                                 model_kwargs=model_params)

    def new_chain(self, prompt_template, model_params):
        return LLMChain(prompt=prompt_template, 
                        llm=self.new_llm(model_params))
    

class HuggingFaceTextgen(HuggingFaceEnv):

    def __init__(self):
        llm = HuggingFaceTextGenInference(
            inference_server_url="http://localhost:8010/",
            max_new_tokens=512,
            top_k=10,
            top_p=0.95,
            typical_p=0.95,
            temperature=0.01,
            repetition_penalty=1.03,
        )


class HuggingFaceLocal(HuggingFaceEnv):

    def __init__(self,
                 repo_id="google/flan-t5-small"):
        super().__init__(repo_id)
        self.pipe = pipeline("text2text-generation",
                              model=self.get_repo(),
                              device="cuda:0",
                              model_kwargs={"torch_dtype":torch.bfloat16})

    def _call(self, prompt, stop=None):
        return self.pipe(prompt, max_length=9999)[0]["generated_text"]

    def _identifying_params(self):
        return {"name_of_model": self.get_repo()}

    def _llm_type(self):
        return "custom"
    

class HuggingFaceTextgen(HuggingFaceEnv):

    def __init__(self):
        super().__init__()

    def forward(self, context, temperature=.5, max_length=64):
        endpoint = "https://fe470eotbeyrto13.us-east-1.aws.endpoints.huggingface.cloud"
        data = {"inputs": str(context)}
        headers = {"Authorization": "Bearer " + self.hugging_face_aut,
                  "Content-type": "application/json"}
        return requests.post(endpoint, data=json.dumps(data), headers=headers).json()
