from typing import Optional
from pydantic import BaseModel

    
class User(BaseModel):
    username: str
    password: str
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    email: str
    phone_number: Optional[str] = None
    is_super_admin: bool = False

class UserInDB(User):
    hashed_password: str
    