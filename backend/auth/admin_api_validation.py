from fastapi import Header
import dotenv
import os

dotenv.load_dotenv()
ADMIN_API_KEY = os.getenv('ADMIN_API_KEY')

def validate_admin_api_key(x_api_key: str = Header(None)):
    print(f"Validating admin API key: {x_api_key}")
    if x_api_key is None or x_api_key != ADMIN_API_KEY:
        return False
    return True