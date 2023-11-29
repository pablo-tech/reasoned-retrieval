import concurrent.futures
import uuid
import time

from collections import namedtuple

import langchain


### AnsweredContent
''' For a given text, each model provides an answer
'''
fields = ['model_answers', 'model_latency', 'exception_text', 'payload_id', 'content_id']
AnsweredContent = namedtuple('AnsweredContent', fields, defaults =  ({}, {}, '', '', ''))


class ExecutionPlayload():

    def __init__(self, 
                 model_payload,
                 executable_names, 
                 payload_id=str(uuid.uuid4()),
                 content_id=str(uuid.uuid4())):
        self.model_payload = model_payload
        self.executable_names = executable_names
        self.payload_id = payload_id
        self.content_id = content_id

    def get_model_payload(self):
        return self.model_payload
    
    def get_executable_names(self):
        return self.executable_names

    def get_payload_id(self):
        return self.payload_id

    def get_content_id(self):
        return self.content_id
    

class QueryExecutor():

    def __init__(self, model_factory, payload_answers_func):
        self.model_factory = model_factory
        self.payload_answers_func = payload_answers_func

    def max_workers(self, execution_payloads):
        max_workers = 5
        for payload in execution_payloads:
            max_workers += len(payload.get_executable_names()) 
        return max_workers            

    def execute_payloads(self, execution_payloads):
        payload_answers = {}
        if len(execution_payloads) == 0:
            print("NOTHING_TO_DO... count=" + str(len(execution_payloads)))
            return []
        max_workers = self.max_workers(execution_payloads)        
        with concurrent.futures.ThreadPoolExecutor(max_workers) as thread_executor:
            for execution_payload in execution_payloads:
              try:
                  thread_executor.submit(self.payload_answers_func, execution_payload, payload_answers)
              except:
                  print("UNABLE_TO_THREAD=" + str(execution_payload.content_context))
        return list(payload_answers.values())


class ModelExecutor(QueryExecutor):

    def __init__(self, model_factory):
        super().__init__(model_factory, self.payload_model_answers)

    def payload_model_answers(self, 
                              execution_payload:ExecutionPlayload, 
                              payload_answers):
        model_answers = {}
        model_latency = {}
        for executable_name in execution_payload.get_executable_names():
                try:
                    
                    qna_model = self.model_factory.new_model(executable_name)
                    model_payload = execution_payload.get_model_payload()
                    time_start = time.time()
                    model_answer = qna_model.invoke(model_payload)
                    time_end = time.time()
                    if isinstance(qna_model, langchain.chat_models.ChatOpenAI):
                        model_answer = model_answer.content
                    print(f"""qna_model={type(qna_model)} executable_name={executable_name} payload={model_payload} model_answer={model_answer}""")
                    model_answers[executable_name] = model_answer
                    model_latency[executable_name] = "{:0.2f}".format(time_end-time_start)                    
                except Exception as e:
                    print("ERROR_COMPOSING_ANSWER=" + str(e))

        content_answers = AnsweredContent(model_answers = model_answers, 
                                          model_latency = model_latency,
                                          payload_id = execution_payload.get_payload_id(),
                                          content_id = execution_payload.get_content_id())
        payload_answers[execution_payload.payload_id] = content_answers    

    # def new_payload(self, model_payload, executable_choice):
    #     return ExecutionPlayload(model_payload, executable_choice, payload_id = str(uuid.uuid4()))        



    

    