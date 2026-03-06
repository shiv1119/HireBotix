from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (AuthenticationException,
                                 AuthorizationException, ConflictException,
                                 NotFoundException)
from app.core.jwt import create_access_token, create_refresh_token
from app.core.security import hash_password, verify_password
from app.models.users import User

ALGORITHM = "HS256"


async def register_user(db: AsyncSession, email: str, password: str):
    result = await db.execute(
        select(User).where(User.email == email, User.is_deleted == False)
    )
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise ConflictException("Email already registered")
    new_user = User(email=email, password=hash_password(password))
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    access_token = create_access_token({"user_id": new_user.id})
    refresh_token = create_refresh_token({"user_id": new_user.id})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


async def login_user(db: AsyncSession, email: str, password: str):
    result = await db.execute(
        select(User).where(User.email == email, User.is_deleted == False)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise AuthenticationException()
    if not verify_password(password, user.password):
        raise AuthenticationException()
    if not user.is_active:
        raise AuthorizationException("User account disabled")
    access_token = create_access_token({"user_id": user.id})
    refresh_token = create_refresh_token({"user_id": user.id})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


async def refresh_access_token(db: AsyncSession, refresh_token: str):
    try:
        payload = jwt.decode(
            refresh_token, settings.REFRESH_SECRET_KEY, algorithms=[ALGORITHM]
        )
        if payload.get("type") != "refresh":
            raise AuthenticationException("Invalid token type")
        user_id = payload.get("user_id")
        if not user_id:
            raise AuthenticationException("Invalid token")
    except JWTError:
        raise AuthenticationException("Invalid refresh token")
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_deleted == False)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException("User not found")
    if not user.is_active:
        raise AuthorizationException("User disabled")
    new_access_token = create_access_token({"user_id": user.id})

    return {"access_token": new_access_token, "token_type": "bearer"}
