import os
import pandas as pd
import csv


class FaqReader():

    ROW_COL = "row"

    def __init__(self, directory_path):
        self.directory_path = directory_path
        self.directory_files = os.listdir(self.directory_path)

    def read_faq(self):
        named_dfs = self.read_drive(self.directory_files)
        self.faq_xls = self.read_df(named_dfs)
        return self.faq_xls

    def read_drive(self, directory_files):
        dfs = []
        for file_name in directory_files:
            df = pd.read_excel(self.directory_path + file_name)
            print(file_name)
            dfs.append((file_name, df))
        return dfs
    
    def read_df(self, dfs):
        xls = []
        for file_name, df in dfs:
          i = 0
          for index, row in df.iterrows():
            try:
              example = {}
              q = row.iloc[0]
              a = row.iloc[1]
              example["user_question"] = q
              example["agent_answer"] = a
              example["source"] = file_name
              example[FaqReader.ROW_COL] = i
              xls.append(example)
              i += 1
            except Exception as e:
              print(str(file_name), str(e), row)
        return xls


class FaqData():
   
    def __init__(self, directory_path='/content/drive/MyDrive/StanfordLLM/qa_data/faq_qa/'):
        self.directory_path = directory_path
        self.reader = FaqReader(directory_path+'faq_source/')

    def get_faq(self):
        return self.reader.read_faq()
    
    def export_faq(self, faqs):
        data_file = open(self.directory_path+'joined_faq.csv', 'w')
        csv_writer = csv.writer(data_file)
        for faq in faqs:
            text = faq['user_question'] + "? " + faq['agent_answer']
            text.replace("??", "?")
            csv_writer.writerow([text])

    def get_pharmacy(self):
        xls = self.get_faq()
        return [ item for item in xls
                    if "prescription" in item["user_question"] or
                       "medicine" in item["user_question"] or
                       "pharmacy" in item["user_question"] ]

    def get_bulleted(self):
        xls = self.get_faq()
        bulleted_examples = [example for example in xls
                     if "1." in example['agent_answer'] or
                        "- " in example['agent_answer'] or
                        "i." in example['agent_answer']]
        return bulleted_examples
    
    def get_unbullted(self):
        xls = self.get_faq()
        bulleted = self.get_bulleted()
        unbulleted_examples = [example for example in xls
                       if example not in bulleted]
        return unbulleted_examples