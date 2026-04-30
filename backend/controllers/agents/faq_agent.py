import sys
import os

sys.path.append(os.path.join(os.getcwd()))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from config.mypinecone import MyPinecone
from controllers.query_saving import save_query
from models.history_query import HistoryQuery
import datetime
import json
import asyncio

class FAQAgent:
    def __init__(self):
        self.pinecone = MyPinecone()
    
    async def get_answer(self, query, category, index_name = "faqs", top_k=1, filter = None, include_values=False, include_metadata=True):
        found_doc = self.pinecone.search(index_name, query, top_k, filter, include_values, include_metadata)
        if found_doc.status_code == 200:
            output_search = json.loads(found_doc.body)
            try:
                matches = output_search['results']['matches']
                if matches[0]['score'] > 0.87:
                    return matches[0].get('metadata')
                else:
                    new_history_query_data = HistoryQuery(
                        query = query,
                        category=category,
                        timestamp = datetime.datetime.now().isoformat(),
                        clustered=False
                    )
                    new_query = await save_query(new_history_query_data)
                    if new_query.get('error'):
                        return f'Error from FAQAgent with MongoDB: {new_query.get("error")}'
                    else:
                        return "Not found"
            except Exception:
                return "Not found"
        else:
            raise RuntimeError(f"Error from FAQAgent: {json.loads(found_doc.body).get('message')}")
        
        
        
##################### TEST #####################
# faq_agent = FAQAgent()
# filterout = {"tags": {"$in": ["study permit", "visa"]}}
# query = "Can I extend my stay as a student?"

# async def test():
#     answer = await faq_agent.get_answer(query, "study permit", filter=filterout)
#     print(answer)
    
# asyncio.run(test())

    