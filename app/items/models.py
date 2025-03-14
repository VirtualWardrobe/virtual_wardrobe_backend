from pydantic import BaseModel
from typing import Optional

class ItemCreate(BaseModel):
    category: str
    type: str
    brand: str
    size: str
    color: str
    userId: str
    image: Optional[str] = None

class ItemResponse(BaseModel):
    id: str
    category: str
    type: str
    brand: str
    size: str
    color: str
    userId: str
    image: str

class ItemUpdate(BaseModel):
    category: Optional[str] = None
    type: Optional[str] = None
    brand: Optional[str] = None
    size: Optional[str] = None
    color: Optional[str] = None
    userId: Optional[str] = None
    image: Optional[str] = None
