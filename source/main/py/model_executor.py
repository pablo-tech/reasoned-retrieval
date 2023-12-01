import concurrent.futures
import uuid
import time

from collections import namedtuple, defaultdict

import langchain


### AnsweredContent
''' For a given text, each model provides an answer
'''
fields = ['model_answers', 'model_latency', 'payload_id', 'exception_text']
AnsweredContent = namedtuple('AnsweredContent', fields, defaults =  ({}, {}, '', ''))


class ExecutionPlayload():

    def __init__(self, 
                 model_payload,
                 executable_names, 
                 payload_id=str(uuid.uuid4())):
        self.model_payload = model_payload
        self.executable_models = { str(uuid.uuid4()): e for e in executable_names }
        self.payload_id = payload_id

    def get_model_payload(self):
        return self.model_payload
    
    def get_payload_id(self):
        return self.payload_id
    
    def get_executable_ids(self):
        return list(self.executable_models.keys())
    
    def get_executable_name(self, key):
        return self.executable_models[key]
    
    def get_executable_count(self):
        return len(self.executable_models)


class PayloadFactory():

    def __init__(self,
                 model_payload,
                 executable_names):
        self.payloads = [ExecutionPlayload(model_payload,
                                           [executable]) 
                         for executable in executable_names] 

    def get_payloads(self):
        return self.payloads


class QueryExecutor():
    '''' Parallelism: payload-level
    '''
    def __init__(self, model_factory, payload_answers_func):
        self.model_factory = model_factory
        self.payload_answers_func = payload_answers_func

    def max_workers(self, execution_payloads):
        max_workers = 1 + len(execution_payloads)
        return max_workers            

    def execute_payloads(self, execution_payloads):
        payload_answers = {}
        if len(execution_payloads) == 0:
            print("NOTHING_TO_DO...")
            return []
        max_workers = self.max_workers(execution_payloads)        
        with concurrent.futures.ThreadPoolExecutor(max_workers) as thread_executor:
            for execution_payload in execution_payloads:
                self.execute_payload(thread_executor, 
                                     execution_payload, 
                                     payload_answers)
        return list(payload_answers.values())
    
    def execute_payload(self, thread_executor:concurrent.futures.ThreadPoolExecutor, 
                        execution_payload:ExecutionPlayload, payload_answers):
        try:
            thread_executor.submit(self.payload_answers_func, execution_payload, payload_answers)
        except:
            print("UNABLE_TO_THREAD=" + str(execution_payload.get_payload_id()))


class ModelExecutor(QueryExecutor):
    ''' Sequential: executable runs
    '''
    def __init__(self, model_factory):
        super().__init__(model_factory, self.payload_model_answers)

    def payload_model_answers(self, 
                              execution_payload:ExecutionPlayload, 
                              payload_answers):
        model_answers = {}
        model_latency = {}
        for executable_id in execution_payload.get_executable_ids():
                try: 
                    executable_name = execution_payload.get_executable_name(executable_id)
                    qna_model = self.model_factory.get_model(executable_name)
                    model_payload = execution_payload.get_model_payload()
                    time_start = time.time()
                    model_answer = qna_model.invoke(model_payload)
                    time_end = time.time()
                    if isinstance(qna_model, langchain.chat_models.ChatOpenAI):
                        model_answer = model_answer.content
                    # print(f"""qna_model={type(qna_model)} executable_name={executable_name} payload={model_payload} model_answer={model_answer}""")
                    model_answers[executable_id] = model_answer
                    model_latency[executable_id] = "{:0.2f}".format(time_end-time_start)
                    # print("model_answers=>"+str(model_answers))                    
                except Exception as e:
                    print("ERROR_COMPOSING_ANSWER=" + str(e))

        content_answers = AnsweredContent(model_answers = model_answers, 
                                          model_latency = model_latency,
                                          payload_id = execution_payload.get_payload_id())
        payload_answers[execution_payload.get_payload_id()] = content_answers    


class QueryExecutor(ModelExecutor):

    def __init__(self, model_factory):
        super().__init__(model_factory)

    def execute_queries(self, execution_payloads):
        answered_contents = self.execute_payloads(execution_payloads)
        final_state = set()
        final_items = []
        for answered_content in answered_contents:
            try:
                for domain, answers in answered_content.model_answers.items():
                    # print(f"""domain=>{domain} answers={answers}""")
                    for state_items in answers:
                        user_state = state_items['user_state']
                        if  user_state != '':
                            final_state.add(user_state)
                        state_items = state_items['result_items']
                        if len(state_items) > 0:
                            final_items.extend(state_items)
            except Exception as e:
                print("DOMAIN_EXECUTION_ERROR="+str(e))
        return final_state, final_items