from fastapi import Depends, HTTPException, status, Request
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from typing import Optional
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from fastapi.responses import RedirectResponse
from database import crud, get_db, models

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    user = crud.get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user

async def get_current_user_from_cookie(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return None

    if token.startswith("Bearer "):
        token = token.split(" ")[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    
    user = crud.get_user_by_username(db, username=username)
    return user

def require_role(required_role: str):
    """Фабрика зависимостей для проверки роли пользователя."""
    async def role_checker(request: Request, user: models.User = Depends(get_current_user_from_cookie)):
        if not user:
            return RedirectResponse(url="/?error=Требуется аутентификация", status_code=303)
        if user.role != required_role and user.role != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail=f"Доступ запрещен. Требуется роль: {required_role}"
            )
        return user
    return role_checker