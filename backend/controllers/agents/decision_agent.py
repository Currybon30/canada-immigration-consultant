import os
import csv

class DecisionAgent:
    def __init__(self, datapath=None):
        if datapath==None:
            self.path = os.path.dirname(os.path.abspath("__file__"))
        else:
            self.path = datapath
        self.dataset_l1_files = ['Visa_l1.csv', 'SP_l1.csv', 'PGWP_l1.csv', 'CRS_l1.csv']
        self.dataset_l2_files = ['Visa_l2.csv', 'SP_l2.csv', 'PGWP_l2.csv', 'CRS_l2.csv']
        self.classes = {0:"visa", 1:"study permit", 2:"pgwp", 3:"crs"}
        self.dataset_l1 = {}
        self.dataset_l2 = {}
        
        #Load keywords from each file and store them in a dictionary
        for index, file in enumerate(self.dataset_l1_files):
            file = os.path.join(self.path, 'utils', file)
            if os.path.exists(file):
                class_name = self.classes[index]
                self.dataset_l1[class_name] = self.load_keywords(file)
            else:
                print(f"File {file} not found.")
        for index, file in enumerate(self.dataset_l2_files):
            file = os.path.join(self.path, 'utils', file)
            if os.path.exists(file):
                class_name = self.classes[index]
                self.dataset_l2[class_name] = self.load_keywords(file)
            else:
                print(f"File {file} not found.")
                
    def load_keywords(self, file_path):
        with open(file_path, 'r') as file:
            reader = csv.reader(file)
            keywords = [row[0] for row in reader]
        return keywords
    
    def count(self, question_tokens, keywords):
        num=0
        for token in question_tokens:
            if token in keywords:
                num += 1
        return num
    
    def contains_string(self, question, word_list):
        question_lower = question.lower()
        for text in word_list:
            if text in question_lower:
                return True
        return False
    
    #Define a function to classify a user question based on keyword matching
    def classify_question(self, question):
        question_words = set(question.lower().split())
        predicted_class_name = "Unknown"
        num=-1
        for class_name, keywords in self.dataset_l2.items():
            if(self.contains_string(question, self.dataset_l1[class_name])):
                n_num = 3
            else:
                n_num = 0
            n_num += self.count(question_words, keywords)
            if n_num > num:
                predicted_class_name = class_name
                num= n_num
        return predicted_class_name
    
    def is_the_query_related_to_study_permit_pgwp_or_visa(self, question):
        predicted_class_name = self.classify_question(question)
        class_idx = (list(self.classes.keys())[list(self.classes.values()).index(predicted_class_name)])
        return class_idx<=2



## TESTING THE DECISION AGENT ###
# question = "How to apply for CRS score?"   
# da = DecisionAgent()
# category = da.classify_question(question)
# answer = da.is_the_query_related_to_study_permit_pgwp_or_visa(question)
# print(f'Is the query related to "study permit", "pgwp" or "visa"? {answer}')
# print(f'The query is related to: {category}')