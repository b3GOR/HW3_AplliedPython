from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class User(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    
    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str



class LinkRequest(BaseModel):
    long_link: str = Field(..., example="https://example.com")
    alias: Optional[str] = Field(None, example="my-short-url")
    expires_at: Optional[datetime] = Field(None, example="2025-12-31T23:59:59")

class LinkResponse(BaseModel):
    long_link: str
    short_link: str

class LinkStats(BaseModel):
    original_url: str
    created_at: datetime
    access_count: int
    last_access: Optional[datetime] = None
    expires_at: Optional[datetime] = None




class TokenData(BaseModel):
    username: Optional[str] = None

class LinkUpdate(BaseModel):
    new_short_code: str = Field(...,description="Новый short_code для замены")