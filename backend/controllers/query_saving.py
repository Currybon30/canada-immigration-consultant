"""
This file contains the functions that are used to save the querries to build FAQs.
Any querries that are not matched with the existing FAQs are saved in the database.
"""
import os
import sys
from bson import ObjectId

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models.history_query import HistoryQuery
from config.mongodb import get_history_query_collection


async def save_query(query: HistoryQuery):
    """
    This function saves the query to the database.
    """
    try:
        history_query_collection = get_history_query_collection()
        query_dict = query.model_dump()
        # Check if the query is already in the database
        existing_query = await history_query_collection.find_one({"query": query_dict['query']})
        if existing_query:
            return existing_query
        new_history_query = await history_query_collection.insert_one(query_dict)
        created_query = await history_query_collection.find_one({"_id": new_history_query.inserted_id})
        return created_query
    
    except Exception as e:
        return {"error": str(e)}
    
async def get_queries_clustered_by_category(category: str):
    """
    This function gets the queries that are clustered by category.
    """
    try:
        history_query_collection = get_history_query_collection()
        queries = await history_query_collection.find({"category": category, "clustered": True}).to_list(length=100)
        return queries
    
    except Exception as e:
        return {"error": str(e)}

async def get_queries_unclustered_by_category(category: str):
    """
    This function gets the queries that are not clustered by category.
    """
    try:
        history_query_collection = get_history_query_collection()
        queries = await history_query_collection.find({"category": category, "clustered": False}).to_list(length=100)
        return queries
    
    except Exception as e:
        return {"error": str(e)}
    
async def update_queries(ids: list, clustered: bool):
    try:
        history_query_collection = get_history_query_collection()
        for id in ids:
            # Convert string ID to ObjectId
            if isinstance(id, str):
                object_id = ObjectId(id)
            await history_query_collection.update_one({"_id": object_id}, {"$set": {"clustered": clustered}})
        return {"message": "Queries updated successfully"}
    except Exception as e:
        return {"error": str(e)}
    
async def delete_queries(ids: list):
    try:
        history_query_collection = get_history_query_collection()
        for id in ids:
            # Convert string ID to ObjectId
            if isinstance(id, str):
                object_id = ObjectId(id)
            await history_query_collection.delete_one({"_id": object_id})
        return {"message": "Queries deleted successfully"}
    except Exception as e:
        return {"error": str(e)}
    
    
####! Test the function ####
# if __name__ == "__main__":
#     import asyncio
    
#     query = HistoryQuery(
#         query = "How to apply for a study permit?",
#         timestamp="2022-10-10 10:10:10"
#     )
    
#     result = asyncio.run(save_query(query))
#     print(result)
    