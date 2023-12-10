import concurrent.futures 
import uuid
import time

from collections import namedtuple, defaultdict

import langchain


### AnsweredContent
''' For a given text, each model provides an answer
'''
fields = ['model_answer', 'model_latency', 'exception_text']
AnsweredContent = namedtuple('AnsweredContent', fields, defaults =  ('', '', ''))


class ExecutionPlayload():

    def __init__(self, 
                 model_payload,
                 executable_model):
        self.model_payload = model_payload
        self.executable_model = executable_model
        self.payload_id = str(uuid.uuid4())

    def get_executable_model(self):
        return self.executable_model
    
    def get_model_payload(self):
        return self.model_payload
    
    def get_payload_id(self):
        return self.payload_id
    

class PayloadFactory():

    def __init__(self,
                 model_payload,
                 executable_models):
        self.payloads = [ExecutionPlayload(model_payload, executable_model) 
                         for executable_model in executable_models] 

    def get_payloads(self):
        return self.payloads


class QueryExecutor():
    '''' Parallelism: payload-level
    '''
    def __init__(self, payload_answers_func):
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
            futures = [self.execute_payload(thread_executor, 
                                            execution_payload, 
                                            payload_answers) 
                        for execution_payload in execution_payloads]
            # print('Waiting for tasks to complete...')
            concurrent.futures.wait(futures)
            # print('All tasks are done!')                
        return payload_answers
        # return list(payload_answers.values())
    
    def execute_payload(self, thread_executor:concurrent.futures.ThreadPoolExecutor, 
                        execution_payload:ExecutionPlayload, payload_answers):
        try:
            return thread_executor.submit(self.payload_answers_func, execution_payload, payload_answers)
        except:
            print("UNABLE_TO_THREAD=" + str(execution_payload.get_payload_id()))


class ModelExecutor(QueryExecutor):
    ''' Runs one model on the payload
    '''
    def __init__(self):
        super().__init__(self.payload_model_answers)

    def payload_model_answers(self, 
                              execution_payload:ExecutionPlayload, 
                              payload_answers):
        model_answer = ''
        model_latency = -1
        try: 
            qna_model = execution_payload.get_executable_model()
            model_payload = execution_payload.get_model_payload()
            time_start = time.time()
            model_answer = qna_model.invoke(model_payload)
            time_end = time.time()
            model_latency = "{:0.2f}".format(time_end-time_start)
            if isinstance(qna_model, langchain.chat_models.ChatOpenAI):
                model_answer = model_answer.content
            # print(f"""qna_model={type(qna_model)} executable_name={executable_name} payload={model_payload} model_answer={model_answer}""")
            # print("model_answers=>"+str(model_answers))                    
        except Exception as e:
            print("ERROR_COMPOSING_ANSWER=" + str(e))

        content_answers = AnsweredContent(model_answer = model_answer, 
                                          model_latency = model_latency)
        payload_answers[execution_payload.get_payload_id()] = content_answers    


class QueryExecutor(ModelExecutor):

    def __init__(self):
        super().__init__()

    def execute_queries(self, execution_payloads):
        answered_contents = self.execute_payloads(execution_payloads)
        final_state = set()
        final_items = []
        for answered_content in answered_contents.values():
            try:
                for state_items in answered_content.model_answer:
                    user_state = state_items['user_state']
                    if  user_state != '':
                        final_state.add(user_state)
                    state_items = state_items['result_items']
                    if len(state_items) > 0:
                        final_items.extend(state_items)
            except Exception as e:
                print("DOMAIN_EXECUTION_ERROR="+str(e))
        return final_state, final_items