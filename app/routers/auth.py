from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.schemas.token import RefreshTokenRequest
from app.schemas.user import UserLogin, UserRegister
from app.services.auth_service import (login_user, refresh_access_token, register_user)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register")
async def register(user: UserRegister, db: Session = Depends(get_db)):
    return await register_user(db, user.email, user.password)

@router.post("/login")
async def login(user: UserLogin, db: Session = Depends(get_db)):
    return await login_user(db, user.email, user.password)

@router.post("/refresh")
async def refresh_token(
        request: RefreshTokenRequest,
        db: Session = Depends(get_db)):
    return await refresh_access_token(db, request.refresh_token)
