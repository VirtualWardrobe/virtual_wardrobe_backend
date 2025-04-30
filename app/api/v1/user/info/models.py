from pydantic import BaseModel
from typing import Optional
from prisma.enums import Role

class UpdateUserInfo(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    profile_pic: Optional[str] = None
    role: Optional[Role] = None
    profile_completion: Optional[int] = None
    is_tutorial_req: Optional[bool] = None
    is_email_verified: Optional[bool] = None
    is_phone_verified: Optional[bool] = None
    is_google_verified: Optional[bool] = None
