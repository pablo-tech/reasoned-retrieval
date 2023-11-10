import json


class HotpotDataset():
    # https://pypi.org/project/wikipedia/

    def __init__(self, completion_llm, is_verbose):
        super().__init__("HOTPOT", completion_llm, is_verbose)
        self.completion_llm = completion_llm
        self.is_verbose = is_verbose
        hotpot_train = '/content/drive/MyDrive/StanfordLLM/hotpot_qa/hotpot_train_v1.1.json'
        with open(hotpot_train) as json_file:
            self.data = json.load(json_file) 

    def get_data(self):
        return self.data

