from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    fname: str
    lname: str
    email: str
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    fname: str
    lname: str
    email: str
    username: str

class ItemCreate(BaseModel):
    category: str
    type: str
    brand: str
    size: str
    color: str
    userId: str

class ItemResponse(BaseModel):
    id: str
    category: str
    type: str
    brand: str
    size: str
    color: str
    image: Optional[str]
    userId: str
