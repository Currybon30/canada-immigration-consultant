import sys
import os

sys.path.append(os.path.join(os.getcwd()))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from config.mypinecone import MyPinecone
import json


class DocumentSearchAgent:
    def __init__(self):
        self.pinecone = MyPinecone()
    
    def find_documents(self, query, index_name = "studypermit-pgwp-visa", top_k=5, filter = None, include_values=False, include_metadata=True):
        found_docs = self.pinecone.search(index_name, query, top_k, filter, include_values, include_metadata)
        if found_docs.status_code == 200:
            return found_docs
        else:
            raise RuntimeError(json.loads(found_docs.body).get('message'))
    
    def filter_answers(self, found_docs):
        output_search = json.loads(found_docs.body)
        answers = []
        for match in output_search['results']['matches']:
            if match['score'] > 0.65:
                answers.append(match.get('metadata'))
            else:
                continue
        if answers:
            return answers
        else:
            return "Answer not found"
            
        
    def combine_matches(self, filtered_answers):
        if filtered_answers != "Answer not found":
            combined_answers = {}
            combined_hyperlinks = []
            combined_text = ""
            combined_ref_links = []
            for answer in filtered_answers:
                for key, value in answer.items():
                    if key == 'hyperlinks':
                        for link in value:
                            combined_hyperlinks.append(link)
                    elif key == 'text':
                        combined_text += " " + answer.get('text')
                    elif key == 'ref_link':
                        if answer.get('ref_link') not in combined_ref_links:
                            combined_ref_links.append(answer.get('ref_link'))
                        
            combined_answers['hyperlinks'] = combined_hyperlinks
            combined_answers['text'] = combined_text
            combined_answers['ref_link'] = combined_ref_links
            return combined_answers
        else:
            return filtered_answers
      
    def get_answers(self,query, index_name = "studypermit-pgwp-visa", top_k=5, filter = None, include_values=False, include_metadata=True):
        found_docs = self.find_documents(query, index_name, top_k, filter, include_values, include_metadata)
        filtered_answers = self.filter_answers(found_docs)
        combined_answers = self.combine_matches(filtered_answers)
        return combined_answers
    
    
# dsa = DocumentSearchAgent()

# query = "How do I apply for a study permit in Canada?"
# answer = dsa.get_answers(query)
# print(answer)