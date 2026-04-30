import warnings
warnings.filterwarnings("ignore")
from sentence_transformers import util
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
import re

class CrossCheckAgent:
    def __init__(self):
        self.embedding_model = HuggingFaceEmbeddings(model_name = "all-MiniLM-L6-v2")
        
        
    def __embed_text(self, text):
        return self.embedding_model.embed_documents([text])
    
    def cross_check(self, llm_answer, ref_answer):
        llm_embedding = self.__embed_text(llm_answer)
        ref_embedding = self.__embed_text(ref_answer)
        similarity_score = util.pytorch_cos_sim(llm_embedding, ref_embedding)
        return similarity_score.item()