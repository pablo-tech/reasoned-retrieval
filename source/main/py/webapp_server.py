#model related 
from llm_executor import ContextValues
from llm_agent import PipelinedAgent, AgentFactory
from tool_factory import ToolFactory
from llm_executor import PipelinedExecutor
from llm_memory import LlmMemory
from llm_executor import ExecutorFactory
from tool_math import MathToolFactory
from tool_search import SearchToolFactory
from tool_wikipedia import EncyclopediaToolFactory
from tool_hotpot import HotpotToolFactory
from model_bot import ChatBot
from model_base import OpenaiBase, GoogleBase, MetaBase
from model_huggingface import HuggingFaceAuth
from UI_model_trace import ThoughtTracer

# app related
from flask import Flask, request, jsonify
from flask_cors import CORS
# from flask_restful import Api

app = Flask(__name__)
CORS(app)
# api = Api(app)

# Models

open_ai = OpenaiBase()
# inference_llm_30 = open_ai.inference_llm_30()
chat_llm_40 = open_ai.chat_llm_40() 

# google = GoogleBase()
# palm = google.palm2()
# flan = google.flan_xxl()

# meta = MetaBase()
# llama = meta.llama2_7b_chat_hf()

llms = { 
    "chatgpt_4.0": chat_llm_40,
        #  "chatgpt_3.5": inference_llm_30,
        #  "palm_2": palm,
        #  "flan_xxl": flan,
        #  "llama2_7b": llama
         }

curr_llm = "chatgpt_4.0"
is_verbose = False

# Tracer

tracer = ThoughtTracer(llms[curr_llm],is_verbose)
# tracer = ThoughtTracer(is_verbose)

@app.route('/message', methods=['POST'])
def process_message():
    message = request.json.get('message', '')
    inference = tracer.hotpot_traces(message)
    response = {"reply": str(inference.agent_answer), 
                "traces": str(inference.run_journey)
                }
    response = jsonify(response)

    return response

if __name__ == '__main__':
    app.run(port=5001,debug=True)

