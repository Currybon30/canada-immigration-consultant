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

mongo_client = None
if MONGO_URI:
    mongo_client = AsyncIOMotorClient(MONGO_URI)
else:
    print("WARNING: MONGO_URI not set")
    
    
@app.on_event("shutdown")
def close_connection():
    if mongo_client:
        mongo_client.close()


@app.get("/")
def health_check():
    return {"status": "ok"}