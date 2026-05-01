from fastapi import Header
import dotenv
import os

dotenv.load_dotenv()
ADMIN_API_KEY = os.getenv('ADMIN_API_KEY')

def validate_admin_api_key(admin_api_key: str = Header(None)):
    if admin_api_key is None or admin_api_key != ADMIN_API_KEY:
        return False
    return True