from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.middleware.cors import CORSMiddleware
from config.mongodb import db
import dotenv
import os


dotenv.load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "https://localhost:8501", "https://canada-immigration-consultant.streamlit.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


MONGO_URI = os.getenv('MONGO_URI')
if not MONGO_URI:
    raise ValueError("MONGO_URI is not set in environment variables")

mongo_client = AsyncIOMotorClient(MONGO_URI)
    
    
@app.on_event("shutdown")
def close_connection():
    print("Closing MongoDB connection...")
    mongo_client.close()

@app.get("/")
def health_check():
    if db is not None:
        return {"status": "ok"}
    else:
        raise HTTPException(status_code=500, detail="Database connection is not established")