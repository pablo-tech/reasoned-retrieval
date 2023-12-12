# ThoughtDistillation
Reasoning and Acting (ReAct) distillation from GPT4 to a small open source model


### Configuration

##### Large Language Models

Within model_base.py:
- Set the GPT api_key in the OpenaiBase class
- Set the GPT api_key in the AzureBase class
- Set the Palm google_api_key in the GoogleBase class 

Within model_huggingface.py:
- Set hugging_face_aut in the HuggingFaceAuth class

##### Information Retrieval: Products Vector Store

Within vector_db.py:
- Set PineCone database api_key in the PineconeEnv class


### Walk-through

##### Contents
- Source: python, noteboks
- Data: producs included, HotPot evaluation dataset not due to size
- Dependencies

#### Evolution
- Notebooks with step-wise development 
- Key notebook with LLM Tool that performs discrete information retrieval
- Also present, LLM conversational agent with tools: future paper

### Demo 

##### Cloning the repo

- Load this notebook in Colab: ReAct-Chatbot-ToolSet.ipynb (found in source/main/ipynb)
- Within the notebook set the google drive work_dir, where GitHome is instantiated
- Running the notebook will clone the repository from GitHub into Google Drive

##### The Demo

- See sub-section Exploratory Query
- See sub-section Complex Direct Queries
