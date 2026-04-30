from pinecone import Pinecone, PineconeException, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
import dotenv
from fastapi.responses import JSONResponse
import os
import json

dotenv.load_dotenv()

class MyPinecone:
    def __init__(self):
        self.__api_key = os.getenv("PINECONE_API_KEY")
        self.pinecone_client = Pinecone(api_key=self.__api_key)
        self.embedding_model = HuggingFaceEmbeddings(model_name = "all-MiniLM-L6-v2")
     
    def list_index_names(self):
        return self.pinecone_client.list_indexes().names()
    
    def create_index(self, index_name, dimension = 384, metric = "cosine", cloud="aws", region="us-east-1"):
        if index_name in self.pinecone_client.list_indexes().names():
            return JSONResponse({'message': f"Index {index_name} already exists"}, status_code=400)
        else:
            self.pinecone_client.create_index(
                name = index_name,
                dimension = dimension,
                metric = metric,
                spec = ServerlessSpec(cloud=cloud, region=region)
            )
            return JSONResponse({'message': f"Index {index_name} created"}, status_code=201)
        
    def insert_data(self, index_name, docs, embeddings = None):
        if index_name not in self.list_index_names():
            return JSONResponse({'message': f"Index {index_name} does not exist"}, status_code=400)
        
        if embeddings is not None:
            self.embedding_model = embeddings
            
            
        self.doc_store = PineconeVectorStore.from_documents(docs, self.embedding_model, index_name = index_name)
        return JSONResponse({'message': f"Data inserted into index {index_name}"}, status_code=201)
    
    def delete_data_by_ofc_doc_id(self, index_name, ofc_doc_id):
        if index_name not in self.list_index_names():
            return JSONResponse({'message': f"Index {index_name} does not exist"}, status_code=400)
        
        index = self.pinecone_client.Index(index_name)
        try:
            filter_stuff = {"ofc_doc_id": ofc_doc_id}
            
            # List vector ids to be deleted
            vector_ids = index.query(id="a44c6712-ed7f-466f-ad32-37b7a0083762", filter=filter_stuff, top_k=9999)
            matches = vector_ids['matches']
            matched_ids = [match['id'] for match in matches]
            
            # Delete vectors
            index.delete(ids=matched_ids)
            
            return JSONResponse({'message': f"ofc_doc_id {ofc_doc_id} has been deleted from index {index_name}"}, status_code=200)
        except PineconeException as e:
            print(e)
            return JSONResponse({'message': f"Error deleting {ofc_doc_id} from index {index_name}"}, status_code=400)
        
    def search(self, index_name, query, top_k=5, filter = None, include_values=False, include_metadata=False):
        if index_name not in self.list_index_names():
            return JSONResponse({'message': f"Index {index_name} does not exist"}, status_code=400)
        
        index = self.pinecone_client.Index(index_name)
        query_vector = self.embedding_model.embed_query(query)
        
        if filter is not None:
            results = index.query(vector=query_vector, top_k=top_k, include_values=include_values, include_metadata=include_metadata, filter=filter)
        else:
            results = index.query(vector=query_vector, top_k=top_k, include_values=include_values, include_metadata=include_metadata)
        results = results.to_dict()
        return JSONResponse({'message': f"Search results for index {index_name}", 'results': results}, status_code=200)
    
    def get_answers_in_text(self, results):
        answers = []
        results = json.loads(results.body)
        matches = results['results']['matches']
        for match in matches:
            answer = match.get('metadata', {}).get('text', '')
            answers.append(answer)
        return JSONResponse({'message': "Answers extracted from search results", 'answers': answers}, status_code=200)