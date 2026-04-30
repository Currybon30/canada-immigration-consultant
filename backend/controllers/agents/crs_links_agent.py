import sys
import os


sys.path.append(os.path.join(os.getcwd()))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.crs_links import crs_links
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

# nltk.download('punkt')
# nltk.download('stopwords')
# nltk.download('punkt_tab')

class CRSLinksAgent:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))

    def preprocess_input(self, user_input):
        tokens = word_tokenize(user_input.lower())
        filtered_tokens = [word for word in tokens if word.isalnum() and word not in self.stop_words]
        return filtered_tokens

    def get_recommendations(self, user_input):
        process_input = self.preprocess_input(user_input)
        recommendation = {}
        max_matches = 0
        best_match = None
        
        for item in crs_links["Comprehensive Ranking System (CRS)"]:
            matches = 0
            for keyword in item["keywords"]:
                if keyword in process_input:
                    matches += 1
            if matches > max_matches:
                max_matches = matches
                best_match = item
        if best_match:
            recommendation[best_match["title"]] = best_match["url"]
        return recommendation if recommendation else "No recommendations found"
    
    
################## TESTING ##################
if __name__ == "__main__":
    agent = CRSLinksAgent()
    user_input = "What is the criteria of Comprehensive Ranking System (CRS)?"
    print(agent.get_recommendations(user_input))
