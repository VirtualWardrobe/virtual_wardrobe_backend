from fastapi import APIRouter, HTTPException, Depends
from prisma import Prisma
from typing import List
from app.api.v1.contacts.models import ContactCreate, ContactResponse
from app.api.v1.user.auth.routes.user import get_current_user
from app.db.prisma_client import PrismaClient


router = APIRouter()


async def get_prisma():
    prisma = await PrismaClient.get_instance()
    return prisma


@router.post("/contacts", response_model=ContactCreate)
async def create_contact(
    contact: ContactCreate,
    db: Prisma = Depends(get_prisma),
    user = Depends(get_current_user)
):
    created_contact = await db.contact.create(
        data=contact.model_dump(exclude_unset=True)
    )
    if not created_contact:
        raise HTTPException(status_code=400, detail="Failed to create contact")
    return created_contact


@router.get("/contacts", response_model=List[ContactResponse])
async def get_contacts(
    db: Prisma = Depends(get_prisma),
    user = Depends(get_current_user)
):
    contacts = await db.contact.find_many()
    return contacts
