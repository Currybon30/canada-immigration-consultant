from sklearn.cluster import KMeans
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from sklearn.metrics import silhouette_score
import numpy as np

class KMeansClustering:
    def __init__(self):
        self.embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.kmeans = None
        self.embeddings = None
        self.labels = None
        self.best_k = None
        self.silhouette_scores = []
        self.questions = None
        self.nearest_questions = None
        
    def embed_questions(self, questions: list):
        self.questions = questions
        if not questions:
            raise ValueError("Questions list is empty.")
        self.embeddings = self.embedding_model.embed_documents(questions)
        return self.embeddings
        
    def create_model(self):
        max_k = min(10, len(self.embeddings) - 1)
        for k in range(2, max_k + 1):
            self.kmeans = KMeans(n_clusters=k, random_state=42)
            self.kmeans.fit(self.embeddings)
            self.labels = self.kmeans.labels_
            silhouette_avg = silhouette_score(self.embeddings, self.labels)
            self.silhouette_scores.append(silhouette_avg)
            
        self.best_k = np.argmax(self.silhouette_scores) + 2
        self.kmeans = KMeans(n_clusters=self.best_k, random_state=42)
        return self.kmeans
    
    def train_model(self):
        self.labels = self.kmeans.fit_predict(self.embeddings)
        return self.labels
    
    def get_questions_nearest_to_centroid(self):
        centroids = self.kmeans.cluster_centers_
        nearest_questions = []
        
        for centroid in centroids:
            distances = np.linalg.norm(self.embeddings - centroid, axis=1)
            nearest_question_index = np.argmin(distances)
            nearest_questions.append(self.questions[nearest_question_index])
            
        self.nearest_questions = nearest_questions
        return self.nearest_questions