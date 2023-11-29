import concurrent.futures
import uuid

from qna_log import LogMessage
from qna_tuple import AnsweredContent


class QueryExecutor():

    def __init__(self):
        pass


class ModelExecutor(QueryExecutor):

    def __init__(self, model_factory):
        super().__init__()
        self.model_factory = model_factory

    def execute_payloads(self, execution_payloads, answer_score_func):
        payload_answers = {}
        if len(execution_payloads) == 0:
            LogMessage.write("NOTHING_TO_DO execution count=" + str(len(execution_payloads)))
            return []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(execution_payloads)) as thread_executor:
            for execution_payload in execution_payloads:
              try:
                  thread_executor.submit(self.payload_model_answers, execution_payload, payload_answers, answer_score_func)
              except:
                  LogMessage.write("UNABLE_TO_THREAD=" + str(execution_payload.content_context))
        return list(payload_answers.values())

    def payload_model_answers(self, execution_payload, payload_answers, answer_score_func):
        model_answers = {}
        for executable_name in execution_payload.executable_choice:
                try:
                    qna_model = self.model_factory.new_model(executable_name)
                    model_answer = qna_model(execution_payload.model_payload)
                    model_answers[executable_name] = model_answer
                except Exception as e:
                    LogMessage.write("ERROR_COMPOSING_ANSWER=" + str(e))

        content_answers = AnsweredContent(content_id = execution_payload.get_content_id(),
                                          model_answers = model_answers, 
                                          score = answer_score_func(model_answers.values()),
                                          payload_id = execution_payload.payload_id)
        payload_answers[execution_payload.payload_id] = content_answers

    def new_payload(self, model_payload, executable_choice):
        return ExecutionPlayload(model_payload, executable_choice, payload_id = str(uuid.uuid4()))        


class ExecutionPlayload():

    def __init__(self, 
                 model_payload,
                 executable_choice, 
                 payload_id):
        self.model_payload = model_payload
        self.executable_choice = executable_choice
        self.payload_id = payload_id

    def get_payload_id(self):
        return self.payload_id

    def get_content_id(self):
        return self.model_payload.get_content_id()