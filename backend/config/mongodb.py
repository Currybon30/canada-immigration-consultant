import dotenv
import os
from motor.motor_asyncio import AsyncIOMotorClient


dotenv.load_dotenv()


MONGO_URI = os.getenv('MONGO_URI')
client = AsyncIOMotorClient(MONGO_URI)

if not MONGO_URI:
    raise ValueError("MONGO_URI is not set in environment variables")
print("Connected to MongoDB")

db = client["immigration-db"]
history_query_collection = db["history_queries"]
user_collection = db["users"]

def get_history_query_collection():
    return history_query_collection

def get_user_collection():
    return user_collection