from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    fname: str
    lname: str
    email: str
    username: str
    password: str

class UserUpdate(BaseModel):
    fname: Optional[str] = None
    lname: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None

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
    userId: str
    image: Optional[str] = None

    class Config:
        orm_mode = True

class ContactCreate(BaseModel):
    name: Optional[str] = None
    email: str
    message: str

class ContactResponse(BaseModel):
    name: Optional[str] = None
    email: str
    message: str
