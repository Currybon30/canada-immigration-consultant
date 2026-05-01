from models.kmeans_clustering import KMeansClustering
from config.mypinecone import MyPinecone
from typing import List
from controllers.query_saving import get_queries_unclustered_by_category, update_queries, delete_queries
import json

async def get_total_unclustered_queries(category: str):
    queries = await get_queries_unclustered_by_category(category)
    
    # Handle case where queries is a dictionary with an error
    if isinstance(queries, dict) and "error" in queries:
        raise RuntimeError(f"Error from get_total_unclustered_queries: {queries['error']}")

    # Ensure queries is always a list
    query_list = queries["queries"] if isinstance(queries, dict) and "queries" in queries else queries
    
    return len(query_list) if query_list else 0

async def get_unclustered_queries(category: str):
    try:
        list_of_ids = []
        list_questions = []
        
        queries = await get_queries_unclustered_by_category(category)

        # Check if queries is an error dictionary
        if isinstance(queries, dict):
            if "error" in queries:
                raise RuntimeError(f"Error from get_unclustered_queries: {queries['error']}")
            queries = queries.get("queries", [])  # Extract actual queries list

        # If queries is empty, return empty lists instead of a string
        if not queries:
            return [], []

        # Extract relevant fields
        for query in queries:
            list_questions.append(query.get('query'))  # Use .get() for safety
            list_of_ids.append(str(query.get('_id')))

        return list_questions, list_of_ids

    except Exception as e:
        raise RuntimeError(f"Error from get_unclustered_queries: {str(e)}")
    

def run_kmeans(list_questions: List[str]):
    try:
        kmeans_clustering = KMeansClustering()
        kmeans_clustering.embed_questions(list_questions)
        kmeans_clustering.create_model()
        kmeans_clustering.train_model()
        nearest_questions = kmeans_clustering.get_questions_nearest_to_centroid()
        return nearest_questions
    except Exception as e:
        raise RuntimeError(f"Error from run_kmeans: {str(e)}")
    
def compare_to_existing_faqs(nearest_questions: List[str], category: str):
    try:
        pending_list = []
        pinecone = MyPinecone()
        index_name = "faqs"
        for question in nearest_questions:
            filter_out = {"tags": {"$in": [category]}}
            found_doc = pinecone.search(index_name, question, 1, filter_out, include_values=False, include_metadata=True)
            if found_doc.status_code == 200:
                output_search = json.loads(found_doc.body)
                if output_search['results']['matches']:
                    matches = output_search['results']['matches']
                    if matches[0]['score'] > 0.87:
                        continue
                    else:
                        pending_list.append(question)
                else:
                    pending_list.append(question)
            else:
                raise RuntimeError(f"Error from compare_to_existing_faqs: {json.loads(found_doc.body).get('message')}")
        return pending_list
    except Exception as e:
        raise RuntimeError(f"Error from compare_to_existing_faqs: {str(e)}")
    
async def update_db(ids: List[str], clustered: bool = True):
    try:
        update_result = await update_queries(ids, clustered=clustered)
        # Check if update_result is a dictionary with an error
        if isinstance(update_result, dict) and "error" in update_result:
            if update_result.get('error'):
                raise RuntimeError(f"Error from update_db: {update_result.get('error')}")
        return update_result
    except Exception as e:
        raise RuntimeError(f"Error from update_db: {str(e)}")
    
async def delete_db(ids: List[str]):
    try:
        delete_result = await delete_queries(ids)
        # Check if delete_result is a dictionary with an error
        if isinstance(delete_result, dict) and "error" in delete_result:
            if delete_result.get('error'):
                raise RuntimeError(f"Error from delete_db: {delete_result.get('error')}")
        return "Queries deleted successfully"
    except Exception as e:
        raise RuntimeError(f"Error from delete_db: {str(e)}")
    

async def cluster_faqs_pipeline(category: str):
    try:
        list_questions, list_of_ids = await get_unclustered_queries(category)
        if not list_questions:
            return "No unclustered queries found"
        if not isinstance(list_questions, list):
            return f'{list_questions} should be a list of questions'
        if not isinstance(list_of_ids, list):
            return f'{list_of_ids} should be a list of ids'
        nearest_questions = run_kmeans(list_questions)
        pending_list = compare_to_existing_faqs(nearest_questions, category)
        if pending_list:
            pending_new_faqs = {}
            pending_new_faqs['category'] = category
            pending_new_faqs['questions'] = pending_list
            pending_new_faqs['ids'] = list_of_ids
            await update_db(list_of_ids, clustered=True)
            return pending_new_faqs
        else:
            await delete_db(list_of_ids)
            return "No pending questions to answers after clustering"
    except Exception as e:
        raise RuntimeError(f"Error from cluster_faqs_pipeline: {str(e)}")