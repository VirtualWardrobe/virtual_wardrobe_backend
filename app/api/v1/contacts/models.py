from pydantic import BaseModel
from typing import Optional

class Contact(BaseModel):
    name: Optional[str] = None
    email: str
    message: str
