from app import app
from views.faq_saving import router as faq_saving_router
from views.pdf_saving import router as pdf_saving_router
from views.login import router as login_router
from views.signup import router as signup_router
from views.manage_accounts import router as manage_accounts_router
from views.security import router as security_router
from views.chatbot import router as chatbot_router

app.include_router(faq_saving_router)
app.include_router(pdf_saving_router)
app.include_router(login_router)
app.include_router(signup_router)
app.include_router(manage_accounts_router)
app.include_router(security_router)
app.include_router(chatbot_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)