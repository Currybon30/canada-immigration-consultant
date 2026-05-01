from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.middleware.cors import CORSMiddleware
import dotenv
import os
from views.faq_saving import router as faq_saving_router
from views.pdf_saving import router as pdf_saving_router #
from views.login import router as login_router
from views.signup import router as signup_router
from views.manage_accounts import router as manage_accounts_router #
from views.security import router as security_router #
from views.chatbot import router as chatbot_router


dotenv.load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "https://localhost:8501", "https://iris-canada.streamlit.app"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


app.include_router(faq_saving_router)
app.include_router(pdf_saving_router)
app.include_router(login_router)
app.include_router(signup_router)
app.include_router(manage_accounts_router)
app.include_router(security_router)
app.include_router(chatbot_router)

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