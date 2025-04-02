import asyncio
import json
from typing import Optional
from fastapi import Depends, HTTPException,status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime,timedelta, timezone
from passlib.context import CryptContext
import shortuuid
from sqlalchemy.orm import Session
from pydantic import BaseModel

from config import ALGORITHM, MAX_SIZE, SECRET_KEY,redis_client
from db import LinkDB, SessionLocal, UserDB
from validation import TokenData






pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db: Session, username: str):
    return db.query(UserDB).filter(UserDB.username == username).first()

def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if token is None:
        return None
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        token_data = TokenData(username=username)
    except JWTError:
        return None
    user = get_user(db, username=token_data.username)
    if user is None:
        return None
    return user

async def get_current_active_user(current_user: UserDB = Depends(get_current_user)):
    if current_user is None:
        return None
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def generate_short_link(long_link):
    gen_short_link = shortuuid.uuid()[:8]  
    return long_link, gen_short_link

def cache_link(short_code, original_url, access_count=0):
    # Сохраняем ссылку в хэше
    redis_client.hset(short_code, "original_url", original_url)
    redis_client.hset(short_code, "access_count", access_count)
    
    # Добавляем в сортированный набор с счетчиком доступа как score
    redis_client.zadd('links_by_access', {short_code: access_count})
    
    # Проверяем размер кэша и при необходимости удаляем
    check_cache_size()

def get_cached_link(short_code):
    original_url = redis_client.hget(short_code, "original_url")
    if original_url:
        # Увеличиваем счетчик доступа при каждом обращении
        update_access_count(short_code)
        return original_url
    return None

def update_access_count(short_code):
    # Увеличиваем счетчик в хэше
    new_count = redis_client.hincrby(short_code, "access_count", 1)
    
    # Обновляем значение в сортированном наборе
    redis_client.zadd('links_by_access', {short_code: new_count})

def delete_cache_link(short_code):
    # Удаляем из сортированного набора
    redis_client.zrem('links_by_access', short_code)
    
    # Удаляем хэш
    redis_client.delete(short_code)

def check_cache_size():
    # Проверяем количество элементов в кэше
    cache_size = redis_client.zcard('links_by_access')
    
    # Если кэш переполнен, удаляем наименее популярные ссылки
    if cache_size > MAX_SIZE:
        # Получаем наименее популярные ссылки (с наименьшим счетчиком)
        to_remove = redis_client.zrange('links_by_access', 0, cache_size - MAX_SIZE - 1)
        
        for short_code in to_remove:
            delete_cache_link(short_code)


def delete_expired_links():
        db = SessionLocal()
        current_time = datetime.now(timezone.utc)
        expired_links = db.query(LinkDB).filter(
            LinkDB.expires_at.isnot(None),
            LinkDB.expires_at < current_time
        ).all()
        
        for link in expired_links:
            delete_cache_link(link.short_code)
            db.delete(link)
        
        db.commit()
        db.close()

        return f"Deleted {len(expired_links)} expired links"


    
 

