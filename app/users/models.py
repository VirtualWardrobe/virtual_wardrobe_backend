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

class UserUpdate(BaseModel):
    fname: Optional[str] = None
    lname: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
