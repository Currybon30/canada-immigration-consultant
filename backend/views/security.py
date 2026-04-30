from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Annotated
from models.user import User
from fastapi.responses import JSONResponse
from config.mongodb import user_collection
from controllers.users import update_user_password
from auth.user_authentication import get_current_user, verify_password, hash_password

router = APIRouter(prefix="/api")

@router.put("/users/update-password")
async def update_password(current_user: Annotated[User, Depends(get_current_user)], new_password: str = Body(...), current_password: str = Body(...)):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    
    if not verify_password(current_password, current_user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect current password.")
    
    hashed_password = hash_password(new_password)
    response = await update_user_password(user_collection, current_user["username"], hashed_password)
    return JSONResponse(content=response, status_code=200)

