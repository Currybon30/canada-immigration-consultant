from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from models.user import User
from fastapi.responses import JSONResponse
from config.mongodb import user_collection
from controllers.users import get_all_users, get_user_by_username, delete_user, update_user_password
from auth.user_authentication import get_current_user, hash_password
from auth.admin_api_validation import validate_admin_api_key

router = APIRouter(prefix="/api")

@router.get("/users")
async def get_users(current_user: Annotated[User, Depends(get_current_user)], x_api_key: str = Depends(validate_admin_api_key)):  
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if current_user is None:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    is_super_admin = current_user['is_super_admin']
    
    if not is_super_admin:
        users = await get_all_users(user_collection, False)
    else:
        users = await get_all_users(user_collection, True)
    
    return JSONResponse(content={"users": users}, status_code=200)

@router.get("/users/{username}")
async def get_user(username: str, current_user: Annotated[User, Depends(get_current_user)], x_api_key: str = Depends(validate_admin_api_key)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if current_user is None:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    is_super_admin = current_user['is_super_admin']
    
    if current_user['username'] == username or is_super_admin:
        user = await get_user_by_username(user_collection, username)
    else:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return JSONResponse(content={"user": user}, status_code=200)

@router.delete("/users/{username}")
async def delete_user_by_username(username: str, current_user: Annotated[User, Depends(get_current_user)], x_api_key: str = Depends(validate_admin_api_key)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if current_user is None:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    is_super_admin = current_user['is_super_admin']
    
    if is_super_admin:
        response = await delete_user(user_collection, username)
    else:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    return JSONResponse(content=response, status_code=200)


@router.put("/users/{username}/reset-password")
async def reset_password(username: str, current_user: Annotated[User, Depends(get_current_user)], x_api_key: str = Depends(validate_admin_api_key)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    if current_user is None:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    is_super_admin = current_user['is_super_admin']
    
    if is_super_admin:
        new_password = "admin123"
        hashed_password = hash_password(new_password)
        response = await update_user_password(user_collection, username, hashed_password)
    else:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    return JSONResponse(content=response, status_code=200)