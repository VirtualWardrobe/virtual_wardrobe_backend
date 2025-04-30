from pydantic import BaseModel
from typing import Optional

class ContactCreate(BaseModel):
    name: Optional[str] = None
    email: str
    message: str

class ContactResponse(BaseModel):
    name: Optional[str] = None
    email: str
    message: str
