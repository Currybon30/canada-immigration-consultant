from auth.user_authentication import authenticate_user, create_access_token
from config.mongodb import user_collection
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from datetime import datetime, timedelta, timezone

router = APIRouter(prefix="/auth")

@router.post("/login")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], response: Response):
    user = await authenticate_user(user_collection=user_collection, username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=60)
    access_token = create_access_token(
        data = {"username": user["username"], 
                "is_super_admin": user["is_super_admin"]},
        expires_delta = access_token_expires
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,  # Set to False for localhost testing
        samesite="None",
        expires=datetime.now(timezone.utc) + access_token_expires
    )
    return {"message": "Login successful"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Logout successful"}
