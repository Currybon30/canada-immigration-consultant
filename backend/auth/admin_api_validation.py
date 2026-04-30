from fastapi import Header
import dotenv
import os

dotenv.load_dotenv()
admin_api_key = os.getenv('ADMIN_API_KEY')

def validate_admin_api_key(x_api_key: str = Header(None)):
    if x_api_key is None or x_api_key != admin_api_key:
        return False
    return True